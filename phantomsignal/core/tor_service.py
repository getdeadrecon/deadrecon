"""
PhantomSignal managed Tor — one click, and Tor is running.

``start`` finds a working Tor or brings one up, in this order:

1. The Tor service the operator configured with ``tor_host`` or ``tor_port``. Nothing
   else is tried: an explicit choice that's down fails rather than being replaced.
2. Tor already running here on 9050, or Tor Browser on 9150, if it really is Tor.
3. A ``tor`` program on this machine, started and stopped by PhantomSignal.
4. The official Tor Expert Bundle, downloaded once and checked against a pinned hash.

Started Tor binds to loopback, keeps its data in ``~/.phantomsignal/tor``, and exits
with this process.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import httpx

from phantomsignal.core.tor import (
    CHECK_URL, DEFAULT_HOST, DEFAULT_PORT, TorUnavailable, forget_verification, tor_enabled, verify_tor,
)

logger = logging.getLogger("phantomsignal.tor")

# From sha256sums-signed-build.txt, signed by the Tor Browser Developers key
# (EF6E 286D DA85 EA2A 4BA7 DE68 4E2C 6E87 9329 8290). Update these with each release.
BUNDLE_VERSION = "16.0"
BUNDLES: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("linux", "x86_64"): ("linux-x86_64", "cc950ebe9acb80188325c3a2cd8817def7dd7237d6fdcd861bb87b234a0cb2fd"),
    ("linux", "aarch64"): ("linux-aarch64", "bed98744e093a0dc3a22be0eecfdce7a33cb36866d3f15fcf011a35bf3513d0d"),
    ("darwin", "arm64"): ("macos-aarch64", "b8da251eccbe9e82f3681ee3af3c97fb4291c4a4e153e5b824bde48a1117cd6a"),
    ("darwin", "x86_64"): ("macos-x86_64", "5b1860215c26f2d408392d1d79e798a2f81d65eb939510bb94c11f237bd0bfc3"),
    ("windows", "amd64"): ("windows-x86_64", "2ee123e9167318a3742778ff704e75f01d4780f05a14522d451fe011011077c4"),
}
_DOWNLOAD_ROOTS = (
    "https://dist.torproject.org/torbrowser",
    "https://archive.torproject.org/tor-package-archive/torbrowser",
)
_MAX_BUNDLE_BYTES = 200 * 1024 * 1024
_BOOTSTRAP_SECONDS = 240.0
_TOR_BROWSER_PORT = 9150
_CONFIGURED_WAIT_SECONDS = 60.0
_BOOTSTRAP = re.compile(r"Bootstrapped (\d+)%[^:]*: (.*)")

OFF, STARTING, READY, FAILED = "off", "starting", "ready", "failed"


def tor_home() -> Path:
    return Path.home() / ".phantomsignal" / "tor"


def _binary_name() -> str:
    return "tor.exe" if sys.platform == "win32" else "tor"


def _bundled_binary() -> Path:
    return tor_home() / BUNDLE_VERSION / "tor" / _binary_name()


def socks_answers(host: str, port: int, timeout: float = 2.0) -> bool:
    """True if something at host:port speaks SOCKS5. It may not be Tor."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(b"\x05\x01\x00")
            return sock.recv(2) == b"\x05\x00"
    except OSError:
        return False


def _port_is_free(port: int) -> bool:
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _is_tor(host: str, port: int) -> bool:
    try:
        with httpx.Client(proxy=f"socks5://{host}:{port}", timeout=30, trust_env=False) as client:
            return client.get(CHECK_URL).json().get("IsTor") is True
    except (httpx.HTTPError, ValueError, OSError):
        return False


def _extract_bundle(archive: Path, version_dir: Path) -> None:
    """Only Tor and its libraries are needed. Everything is written by hand so a bad
    archive can't place files outside the folder."""
    target = version_dir / "tor"
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            parts = member.name.split("/")
            if not member.isfile() or len(parts) != 2 or parts[0] != "tor" or parts[1] in ("", ".", ".."):
                continue
            source = tar.extractfile(member)
            if source is None:
                continue
            path = target / parts[1]
            with source, open(path, "wb") as out:
                shutil.copyfileobj(source, out)
            path.chmod(0o755)
    if sys.platform == "darwin":
        _sign_for_macos(target)


def _sign_for_macos(folder: Path) -> None:
    """The macOS bundle's signature doesn't validate, and Apple Silicon kills such
    programs on launch with no error. Its hash was checked before this step."""
    files = sorted(folder.iterdir(), key=lambda path: path.suffix != ".dylib")
    subprocess.run(["codesign", "--force", "--sign", "-", *map(str, files)],
                   check=True, capture_output=True, timeout=60)


class TorService:
    """Tracks Tor's state for the console and scans. Safe to call from any thread."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._proc: Optional[subprocess.Popen] = None
        self._stopping = False
        self._timed_out = False
        self._auto_port: Optional[int] = None
        self.state = OFF
        self.percent = 0
        self.message = "Tor is off."
        self.source: Optional[str] = None

    def status(self) -> Dict:
        with self._lock:
            return {"state": self.state, "percent": self.percent, "message": self.message, "source": self.source}

    def _set(self, state: Optional[str] = None, percent: Optional[int] = None,
             message: Optional[str] = None, source: Optional[str] = None) -> None:
        with self._lock:
            self.state = state if state is not None else self.state
            self.percent = percent if percent is not None else self.percent
            self.message = message if message is not None else self.message
            self.source = source if source is not None else self.source

    def start(self, config) -> None:
        """Returns at once; Tor comes up in the background."""
        with self._lock:
            if self.state == READY and (self._proc is None or self._proc.poll() is None):
                return
            if self._thread is not None and self._thread.is_alive():
                return
            self._stopping = False
            self._timed_out = False
            self.state, self.percent, self.source = STARTING, 0, None
            self.message = "Starting Tor..."
            self._thread = threading.Thread(target=self._bring_up, args=(config,), daemon=True, name="tor-service")
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stopping = True
            proc, self._proc = self._proc, None
            self.state, self.percent, self.source = OFF, 0, None
            self.message = "Tor is off."
        forget_verification()
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    def wait_ready(self, config, timeout: float = _BOOTSTRAP_SECONDS + 240.0,
                   progress: Optional[Callable[[str], None]] = None) -> None:
        """Blocks until Tor is usable. Raises TorUnavailable if it can't be."""
        if self.status()["state"] != READY:
            self.start(config)
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            current = self.status()
            if current["message"] != last and progress:
                progress(current["message"])
            last = current["message"]
            if current["state"] == READY:
                return
            if current["state"] in (FAILED, OFF):
                raise TorUnavailable(current["message"])
            time.sleep(0.25)
        raise TorUnavailable("Tor didn't finish starting in time. The scan was stopped before contacting the target.")

    def _explicit(self, config) -> bool:
        host = config.get("scraper", "tor_host", default=DEFAULT_HOST)
        port = config.get("scraper", "tor_port", default=DEFAULT_PORT)
        return host != DEFAULT_HOST or (port != DEFAULT_PORT and port != self._auto_port)

    def _use_port(self, config, port: int) -> None:
        self._auto_port = port
        config.set("scraper", "tor_port", value=port)

    def _bring_up(self, config) -> None:
        try:
            if self._explicit(config):
                self._use_configured(config)
                return
            for port, label in ((DEFAULT_PORT, "Tor already running"), (_TOR_BROWSER_PORT, "Tor Browser")):
                if socks_answers(DEFAULT_HOST, port) and _is_tor(DEFAULT_HOST, port):
                    self._use_port(config, port)
                    self._ready(config, label)
                    return
            self._launch(config, self._find_binary())
        except TorUnavailable as exc:
            self._set(FAILED, message=str(exc))
            self._end_process()
        except Exception as exc:  # the console must show why, not hang on "starting"
            logger.exception("Tor failed to start")
            self._set(FAILED, message=f"Tor couldn't start: {exc}")
            self._end_process()

    def _end_process(self) -> None:
        with self._lock:
            proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            proc.terminate()

    def _use_configured(self, config) -> None:
        host = config.get("scraper", "tor_host", default=DEFAULT_HOST)
        port = config.get("scraper", "tor_port", default=DEFAULT_PORT)
        deadline = time.monotonic() + _CONFIGURED_WAIT_SECONDS
        while not socks_answers(host, port):
            if self._stopping:
                return
            if time.monotonic() > deadline:
                raise TorUnavailable(f"Tor isn't answering at the configured address, {host}:{port}. "
                                     "Nothing was sent.")
            time.sleep(2)
        self._ready(config, f"Your Tor service at {host}:{port}")

    def _ready(self, config, source: str) -> None:
        self._set(message="Confirming Tor is working...")
        asyncio.run(verify_tor(config))
        with self._lock:
            if self._stopping:
                return
        self._set(READY, 100, "Tor is on. Scan traffic is confirmed to be using it.", source)

    def _find_binary(self) -> str:
        found = shutil.which("tor")
        if found:
            return found
        bundled = _bundled_binary()
        if bundled.exists():
            return str(bundled)
        self._download_bundle()
        return str(bundled)

    def _download_bundle(self) -> None:
        system, machine = platform.system().lower(), platform.machine().lower()
        bundle = BUNDLES.get((system, machine))
        if bundle is None:
            raise TorUnavailable(f"There's no Tor download for {system} {machine}. Install Tor with your "
                                 "package manager, then turn it on again.")
        name, expected = bundle
        filename = f"tor-expert-bundle-{name}-{BUNDLE_VERSION}.tar.gz"
        home = tor_home()
        home.mkdir(parents=True, exist_ok=True)
        archive = home / f"{filename}.part"
        last_error = "no response"
        for root in _DOWNLOAD_ROOTS:
            try:
                self._fetch(f"{root}/{BUNDLE_VERSION}/{filename}", archive, expected)
                # Installed in one step, so an interrupted setup can't leave half a Tor.
                staging = home / f"{BUNDLE_VERSION}.part"
                shutil.rmtree(staging, ignore_errors=True)
                _extract_bundle(archive, staging)
                shutil.rmtree(home / BUNDLE_VERSION, ignore_errors=True)
                staging.rename(home / BUNDLE_VERSION)
                return
            except (httpx.HTTPError, OSError, ValueError, subprocess.SubprocessError) as exc:
                last_error = str(exc) or type(exc).__name__
                logger.warning("Tor download from %s failed: %s", root, last_error)
            finally:
                archive.unlink(missing_ok=True)
        raise TorUnavailable(f"Tor couldn't be downloaded ({last_error}). Install Tor with your package "
                             "manager, then turn it on again.")

    def _fetch(self, url: str, archive: Path, expected: str) -> None:
        self._set(message="Downloading Tor (first time only)...", percent=0)
        digest = hashlib.sha256()
        received = 0
        with httpx.Client(timeout=60, follow_redirects=True, trust_env=False) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(archive, "wb") as out:
                    for chunk in response.iter_bytes():
                        received += len(chunk)
                        if received > _MAX_BUNDLE_BYTES:
                            raise ValueError("download is larger than expected")
                        digest.update(chunk)
                        out.write(chunk)
        if digest.hexdigest() != expected:
            raise ValueError("download failed its integrity check")

    def _launch(self, config, binary: str) -> None:
        port = DEFAULT_PORT if _port_is_free(DEFAULT_PORT) else _free_port()
        data = tor_home() / "data"
        data.mkdir(parents=True, exist_ok=True)
        data.chmod(0o700)
        command = [
            binary, "-f", os.devnull, "--ignore-missing-torrc",
            "--SocksPort", f"127.0.0.1:{port}", "--ControlPort", "0", "--ClientOnly", "1",
            "--DataDirectory", str(data), "--Log", "notice stdout",
            "--__OwningControllerProcess", str(os.getpid()),
        ]
        env = dict(os.environ)
        if Path(binary).parent != Path(shutil.which("tor") or "").parent:
            env["LD_LIBRARY_PATH"] = str(Path(binary).parent)
        self._set(message="Connecting to the Tor network...", percent=0)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", env=env)
        with self._lock:
            if self._stopping:
                proc.terminate()
                return
            self._proc = proc
        self._use_port(config, port)

        watchdog = threading.Timer(_BOOTSTRAP_SECONDS, self._bootstrap_timed_out, args=(proc,))
        watchdog.daemon = True
        watchdog.start()
        tail = ""
        try:
            for line in proc.stdout:
                if "[warn]" in line or "[err]" in line:
                    tail = line.split("] ", 1)[-1].strip()
                match = _BOOTSTRAP.search(line)
                if not match:
                    continue
                percent = int(match.group(1))
                self._set(percent=percent, message=f"Connecting to the Tor network... {percent}%")
                if percent == 100:
                    watchdog.cancel()
                    self._ready(config, "Tor started by PhantomSignal")
        finally:
            watchdog.cancel()
        proc.wait()
        with self._lock:
            if self._stopping or self._proc is not proc:
                return
            self._proc = None
        was_ready = self.status()["state"] == READY
        forget_verification()
        if was_ready:
            detail = "Tor stopped unexpectedly."
        elif self._timed_out:
            detail = (f"Tor couldn't reach the Tor network in {_BOOTSTRAP_SECONDS / 60:.0f} minutes. Check your "
                      "internet connection. If your network blocks Tor, run your own Tor with bridges.")
        else:
            reason = tail[-200:].rstrip(".") or f"it exited with status {proc.returncode} and no message"
            detail = f"Tor couldn't connect: {reason}."
        self._set(FAILED, 0, f"{detail} Nothing is being sent.")

    def _bootstrap_timed_out(self, proc: subprocess.Popen) -> None:
        if self.status()["state"] == STARTING and proc.poll() is None:
            logger.warning("Tor didn't connect in %.0fs", _BOOTSTRAP_SECONDS)
            self._timed_out = True
            proc.terminate()


service = TorService()


def enable(config) -> None:
    config.set("scraper", "tor_enabled", value=True)
    config.persist()
    service.start(config)


def disable(config) -> None:
    config.set("scraper", "tor_enabled", value=False)
    config.persist()
    service.stop()


def resume(config) -> None:
    """Brings Tor back after a restart if it was left on. A failure stays visible
    until a scan or a click retries it."""
    if tor_enabled(config) and service.status()["state"] == OFF:
        service.start(config)
