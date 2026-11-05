"""
DeadRecon — Best-of-breed external tool adapters, under stealth governance.

Go-native recon tools (ProjectDiscovery's subfinder/naabu/nuclei/katana/tlsx,
masscan) are orders of magnitude faster than pure-Python at internet scale. This
module lets DeadRecon *orchestrate* them when installed, while keeping the
OPSEC flagship intact:

* **Proxy inheritance.** A tool that supports a proxy is handed one from the same
  egress config the stealth client uses (``resolve_egress``), so its traffic is
  masked the same way. Its findings are tagged ``proxied`` when a proxy is in
  play, and honestly ``attributable`` when the tool can't proxy (e.g. masscan's
  raw sockets) or no proxy is configured.
* **Native fallback stays first-class.** ``available()`` gates every adapter on
  ``shutil.which`` — a binary-free ``pip install`` keeps working, falling back to
  the pure-Python module. External tools are always optional, never required.

Adapters subclass ``ExternalTool``, provide the command + an output parser, and
register in the scraper registry with a native fallback.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import asyncio
import re
import logging
import shutil
from typing import Dict, List, Optional
from urllib.parse import urlparse

from deadrecon.core.http import _current_ledger
from deadrecon.core.http import resolve_egress
from deadrecon.core.tor import TOOL_TIMEOUT, tor_enabled
from deadrecon.intel.opsec import OpsecLevel

logger = logging.getLogger("deadrecon.scrapers.external")


def host_only(target: str) -> str:
    """Bare host from a target (strip scheme, path, port, userinfo)."""
    t = (target or "").strip().lower()
    if "://" in t:
        t = urlparse(t).netloc or t
    return t.split("/")[0].split("@")[-1].split(":")[0].lstrip(".")


def as_url(target: str) -> str:
    """A target coerced to a URL; bare hosts default to https."""
    t = (target or "").strip()
    if t.startswith(("http://", "https://")):
        return t
    return f"https://{t}"


FAILURE_TYPE = "external_tool_error"
_URL_CREDENTIALS = re.compile(r"(?<=://)[^/@\s]+@")


def _scrub_credentials(text: str) -> str:
    """Tool output and command lines can contain a proxy URL with its password."""
    return _URL_CREDENTIALS.sub("***@", text)


def host_of(target: str) -> str:
    value = (target or "").strip()
    return urlparse(value if "://" in value else f"//{value}").hostname or value


class ExternalTool:
    """Base for a stealth-governed external CLI tool.

    Subclasses set ``BINARY``, optionally ``PROXY_FLAG`` (the tool's proxy CLI
    flag, e.g. ``-proxy``), and implement ``command()`` + ``parse()``.
    """

    BINARY: str = ""
    PROXY_FLAG: Optional[str] = None   # None → tool cannot proxy (attributable)
    TIMEOUT: float = 300.0
    # Packet captures show this tool still asks the local resolver for some names with
    # a proxy set, and it has no option to send DNS through the proxy.
    LOCAL_DNS: bool = False
    # Packet captures show this tool still connects directly with a proxy set, so a
    # proxy can't be promised to hide the operator.
    BYPASSES_PROXY: bool = False

    def __init__(self, config):
        self.config = config

    @classmethod
    def available(cls) -> bool:
        """Is the tool installed on PATH?"""
        return bool(cls.BINARY) and shutil.which(cls.BINARY) is not None

    def _proxy(self) -> Optional[str]:
        """First real proxy from the shared egress config (tools take one)."""
        egress, _ = resolve_egress(self.config)
        for p in egress:
            if p:
                return p
        return None

    def _opsec_level(self, proxy: Optional[str]) -> OpsecLevel:
        """Honest posture: masked only if the tool actually proxied."""
        if proxy and self.PROXY_FLAG and not self.BYPASSES_PROXY:
            return OpsecLevel.PROXIED
        return OpsecLevel.ATTRIBUTABLE

    def command(self, target: str, opts: Dict) -> List[str]:
        """The tool argv WITHOUT the proxy flag (base appends it)."""
        raise NotImplementedError

    def parse(self, stdout: str, opsec: str) -> List[Dict]:
        """Turn tool stdout into DeadRecon result dicts. ``opsec`` is the
        posture string to stamp into each finding's ``data``."""
        raise NotImplementedError

    def _failure(self, reason: str, opsec: str) -> Dict:
        """A visible finding for a tool that couldn't run, so a failed scan can't be
        mistaken for a clean one."""
        return {
            "type": FAILURE_TYPE,
            "source": self.BINARY,
            "data": {"tool": self.BINARY, "reason": _scrub_credentials(reason)[-500:], "opsec": opsec},
            "confidence": 1.0,
            "relevance_score": 0.3,
            "tags": ["external-tool", "failed"],
        }

    def proxied_args(self) -> List[str]:
        """Extra arguments that keep the tool's traffic on the proxy, when one is set."""
        return []

    def _full_command(self, target: str, opts: Dict, proxy: Optional[str]) -> List[str]:
        cmd = self.command(target, opts)
        if proxy and self.PROXY_FLAG:
            cmd += [self.PROXY_FLAG, proxy] + self.proxied_args()
        return cmd

    async def run(self, target: str, opts: Optional[Dict] = None) -> List[Dict]:
        """Run the tool if present; return [] if not (caller falls back)."""
        opts = opts or {}
        if not self.available():
            return []
        proxy = self._proxy()
        opsec = self._opsec_level(proxy).value
        tor = tor_enabled(self.config)
        if tor and (not self.PROXY_FLAG or self.LOCAL_DNS or self.BYPASSES_PROXY):
            return [self._failure("Not run: this tool would bypass Tor.", opsec)]
        cmd = self._full_command(target, opts, proxy)
        logger.debug("external %s: %s", self.BINARY, _scrub_credentials(" ".join(cmd)))
        ledger = _current_ledger.get()
        if ledger is not None:
            ledger.record_tool_run(self.BINARY, host_of(target),
                                   proxy if self.PROXY_FLAG and not self.BYPASSES_PROXY else None)
            if proxy and self.LOCAL_DNS:
                ledger.local_dns_tools.add(self.BINARY)
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            limit = max(self.TIMEOUT, TOOL_TIMEOUT) if tor else self.TIMEOUT
            out, err = await asyncio.wait_for(proc.communicate(), timeout=limit)
        except asyncio.TimeoutError:
            logger.warning("external %s timed out on %s", self.BINARY, target)
            return [self._failure(f"Timed out after {limit:.0f}s", opsec)]
        except Exception as exc:
            logger.warning("external %s failed on %s: %s", self.BINARY, target,
                           _scrub_credentials(str(exc)))
            return [self._failure(str(exc), opsec)]
        finally:
            if proc is not None and proc.returncode is None:  # timed out or cancelled
                proc.kill()
        results = self.parse(out.decode(errors="replace"), opsec)
        if proc.returncode not in (0, None) and not results:
            reason = err.decode(errors="replace").strip() or f"Exited with status {proc.returncode}"
            logger.warning("external %s exited %s: %s", self.BINARY, proc.returncode,
                           _scrub_credentials(reason)[-300:])
            return [self._failure(reason, opsec)]
        return results


async def run_with_fallback(external: ExternalTool, target: str, opts: Dict,
                            fallback) -> List[Dict]:
    """Run an external tool when available, else the native fallback coroutine.

    ``fallback`` is a zero-arg callable returning the native module's coroutine.
    Keeps external tools strictly optional.
    """
    if external.available():
        results = await external.run(target, opts)
        if results and not any(r.get("type") == FAILURE_TYPE for r in results):
            return results
        # Tool present but produced nothing (or errored) — fall through to native
        # so a flaky binary never silently drops coverage.
    return await fallback()
