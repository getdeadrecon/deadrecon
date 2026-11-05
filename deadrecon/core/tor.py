"""
DeadRecon Tor routing — an exclusive route that fails closed.

With ``scraper.tor_enabled`` on, target-facing traffic goes through the operator's own
Tor or doesn't happen (see ``tor_service`` for how Tor gets started):

* A scan first proves it's on Tor (``verify_tor``) and aborts if it can't.
* Modules that can't use Tor are skipped and reported (``tor_block_reason``).
* Each entry from ``tor_circuits`` has different SOCKS credentials, which Tor uses to
  keep streams on separate circuits. Different targets don't share an exit, and the
  proxy pool's rotation moves a blocked target to a new one.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import asyncio
import json
import logging
import secrets
import time
from typing import Dict, List, Optional
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger("deadrecon.tor")

CHECK_URL = "https://check.torproject.org/api/ip"
MIN_TIMEOUT = 45.0          # building a circuit takes far longer than a direct connect
MODULE_TIMEOUT = 1800.0
TOOL_TIMEOUT = 900.0
VERIFY_SECONDS = 180.0      # Tor accepts connections before it has finished starting
VERIFY_ATTEMPT_SECONDS = 20.0  # a slow circuit shouldn't hold things up: move to the next
VERIFY_RETRY_SECONDS = 3.0
VERIFIED_SECONDS = 600.0
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9050
_CIRCUITS = 16
_SESSION = secrets.token_hex(4)
_verified: Dict[str, float] = {}

# These connect directly, or ask the local resolver for the target's name.
_DIRECT_MODULES = {
    "port_scan": "Port scans can't run over Tor.",
    "port_scan_fast": "Port scans can't run over Tor.",
    "service_enum": "Service probes connect directly to the target.",
    "tls_fingerprint": "tlsx connects directly to the target.",
    "vuln_scan": "nuclei connects directly and asks your local DNS resolver for the target's name.",
}
# The only modules that talk to nothing but an .onion target. The rest send the name
# to third parties such as certificate logs and archives.
_ONION_MODULES = {"web_crawl", "web_crawl_fast", "tech_detect", "api_hunt", "js_mine"}


class TorUnavailable(RuntimeError):
    """The message is safe to show to the operator."""


def tor_enabled(config) -> bool:
    return bool(config.get("scraper", "tor_enabled", default=False))


def tor_proxy_url(config) -> str:
    host = config.get("scraper", "tor_host", default=DEFAULT_HOST) or DEFAULT_HOST
    port = config.get("scraper", "tor_port", default=DEFAULT_PORT) or DEFAULT_PORT
    return f"socks5://{host}:{port}"


def tor_circuits(config) -> List[str]:
    """One egress per circuit. The credentials only tell Tor to keep streams apart."""
    parts = urlsplit(tor_proxy_url(config))
    return [f"socks5://{_SESSION}{i}:x@{parts.netloc}" for i in range(_CIRCUITS)]


def floor_timeout(config, timeout):
    """Raises a numeric timeout that's too short for Tor."""
    if tor_enabled(config) and isinstance(timeout, (int, float)):
        return max(timeout, MIN_TIMEOUT)
    return timeout


def is_onion(host: Optional[str]) -> bool:
    return (host or "").strip("[]").rstrip(".").lower().endswith(".onion")


def target_host(target: str) -> str:
    value = (target or "").strip()
    return urlsplit(value if "://" in value else f"//{value}").hostname or value


def tor_block_reason(module: str) -> Optional[str]:
    return _DIRECT_MODULES.get(module)


def onion_block_reason(module: str) -> Optional[str]:
    if module in _ONION_MODULES:
        return None
    return "This module would send the .onion address to third parties."


async def verify_tor(config) -> None:
    """Raises TorUnavailable unless traffic is reaching the internet through Tor."""
    if not config.get("scraper", "tor_verify", default=True):
        return
    url = tor_proxy_url(config)
    if time.monotonic() - _verified.get(url, -VERIFIED_SECONDS) < VERIFIED_SECONDS:
        return
    last_error = "no response"
    deadline = time.monotonic() + VERIFY_SECONDS
    circuits = tor_circuits(config)
    attempt = -1
    while True:
        attempt += 1
        if attempt:
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(VERIFY_RETRY_SECONDS)
        try:
            async with httpx.AsyncClient(proxy=circuits[attempt % _CIRCUITS],
                                         timeout=VERIFY_ATTEMPT_SECONDS, trust_env=False) as client:
                reply = (await client.get(CHECK_URL)).json()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, OSError) as exc:
            last_error = str(exc) or type(exc).__name__
            continue
        if reply.get("IsTor") is True:
            _verified[url] = time.monotonic()
            return
        raise TorUnavailable(
            f"Tor is on, but {url} isn't routing through Tor: traffic left from "
            f"{reply.get('IP', 'an unknown address')}. The scan was stopped before contacting the target.")
    raise TorUnavailable(
        f"Tor is on, but it couldn't be reached through {url} ({last_error}). "
        "The scan was stopped before contacting the target. Check your internet connection, "
        "then try again.")


def forget_verification() -> None:
    _verified.clear()
