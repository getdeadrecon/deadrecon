"""
DeadRecon network guard — stops scanned sites steering requests inward.

A hostile target can redirect the scanner, or publish links, to addresses only
this machine can reach: above all a cloud metadata service holding credentials.
Two rules apply to direct (unproxied) HTTP:

* Metadata and link-local addresses are never contacted.
* A public site can't redirect to a private address. Operators can still scan
  private targets directly, and redirects between private hosts still work.

Requests can't tell where a URL came from, so a module that follows links found on a
page calls ``link_allowed`` first, which applies the redirect rules to them.

Proxied requests are exempt. They leave from the proxy's network, and resolving
their hosts locally would leak targets to the local DNS resolver.

DNS rebinding is closed for direct HTTP: httpx clients from ``guarded_client`` re-check
and pin each connection, and curl_cffi (TLS impersonation) requests are pinned with
``curl_pin``. Non-HTTP modules such as port scans don't pass through here.

Set ``security.allow_metadata_requests`` (or DEADRECON_ALLOW_METADATA=true) to
deliberately test a metadata service.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlsplit

import httpcore
import httpx

from deadrecon.core.config import config
from deadrecon.core.tor import is_onion

PUBLIC = "public"
PRIVATE = "private"
METADATA = "metadata"

_METADATA_HOSTS = {"metadata.google.internal", "metadata.goog", "instance-data"}
_METADATA_NETS = [
    ipaddress.ip_network("169.254.0.0/16"),    # IPv4 link-local, including AWS/Azure/GCP
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("fd00:ec2::254/128"),  # AWS over IPv6
    ipaddress.ip_network("100.100.100.200/32"),  # Alibaba Cloud
]
_NAT64_NETS = [ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("64:ff9b:1::/48")]
_RESOLVE_TIMEOUT = 3.0
_ENV_PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
_PUBLIC_MEMORY_SECONDS = 300.0
_PUBLIC_MEMORY_LIMIT = 4096
_recently_public: Dict[str, float] = {}


class BlockedDestination(httpx.RequestError):
    """A request was refused by the network guard. Not a transport fault, so the
    stealth client doesn't retry it or penalize the egress."""


def metadata_requests_allowed() -> bool:
    value = os.getenv("DEADRECON_ALLOW_METADATA") or config.get(
        "security", "allow_metadata_requests", default=False)
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def environment_proxy_active() -> bool:
    """httpx and curl honor proxy environment variables. Such traffic is proxied,
    so it's exempt for the same reason as a configured proxy."""
    return any(os.environ.get(name) for name in _ENV_PROXY_VARS)


def _normalize_host(host: Optional[str]) -> str:
    return (host or "").strip("[]").rstrip(".").lower()


def _remember_public(host: str) -> None:
    now = time.monotonic()
    if len(_recently_public) >= _PUBLIC_MEMORY_LIMIT:
        for key in [k for k, seen in _recently_public.items() if now - seen > _PUBLIC_MEMORY_SECONDS]:
            del _recently_public[key]
        if len(_recently_public) >= _PUBLIC_MEMORY_LIMIT:
            _recently_public.clear()
    _recently_public[host] = now


def _was_recently_public(host: str) -> bool:
    seen = _recently_public.get(host)
    return seen is not None and time.monotonic() - seen < _PUBLIC_MEMORY_SECONDS


def _embedded_ipv4(ip: ipaddress.IPv6Address) -> Optional[ipaddress.IPv4Address]:
    """The IPv4 address an IPv6 address carries, for forms that can route to it."""
    if ip.ipv4_mapped or ip.sixtofour:
        return ip.ipv4_mapped or ip.sixtofour
    if int(ip) < 2 ** 32 or any(ip in net for net in _NAT64_NETS):  # IPv4-compatible or NAT64
        return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return None


def classify_ip(value: str) -> str:
    ip = ipaddress.ip_address(value.split("%", 1)[0])
    if isinstance(ip, ipaddress.IPv6Address):
        ip = _embedded_ipv4(ip) or ip
    if any(ip.version == net.version and ip in net for net in _METADATA_NETS):
        return METADATA
    return PUBLIC if ip.is_global else PRIVATE


def _resolve(host: str) -> List[str]:
    # getaddrinfo also normalizes obfuscated forms such as 2852039166 or 0xa9fea9fe.
    return [info[4][0] for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)]


async def classify_host(host: Optional[str]) -> str:
    """The most sensitive class among a host's addresses. A name that can't be
    resolved counts as public, because the connection will fail on its own."""
    host = _normalize_host(host)
    if not host or is_onion(host):
        return PUBLIC
    if host in _METADATA_HOSTS:
        return METADATA
    try:
        return classify_ip(host)
    except ValueError:
        pass
    loop = asyncio.get_running_loop()
    try:
        addresses = await asyncio.wait_for(
            loop.run_in_executor(None, _resolve, host), _RESOLVE_TIMEOUT)
    except (OSError, asyncio.TimeoutError):
        return PUBLIC
    classes = {classify_ip(address) for address in addresses}
    for level in (METADATA, PRIVATE):
        if level in classes:
            return level
    return PUBLIC


async def check_request_url(url: str) -> None:
    host = urlsplit(url).hostname
    if is_onion(host):
        raise BlockedDestination(f"Blocked direct request to {host}: .onion addresses need Tor")
    level = await classify_host(host)
    if level == METADATA and not metadata_requests_allowed():
        raise BlockedDestination(f"Blocked request to a metadata address: {host}")
    if level == PUBLIC:
        _remember_public(_normalize_host(host))


async def check_redirect(origin_url: str, location: str) -> None:
    """Raise if following ``location`` from ``origin_url`` breaks a guard rule."""
    target = urljoin(origin_url, location)
    await check_request_url(target)
    if await classify_host(urlsplit(target).hostname) != PRIVATE:
        return
    if await classify_host(urlsplit(origin_url).hostname) == PUBLIC:
        raise BlockedDestination(
            f"Blocked redirect from {urlsplit(origin_url).hostname} "
            f"to private address {urlsplit(target).hostname}")


async def link_allowed(origin_url: str, link_url: str) -> bool:
    """Whether a direct request may follow a link that ``origin_url`` published. A
    link is held to the redirect rules, since a page can steer a scan with either."""
    try:
        await check_redirect(origin_url, link_url)
    except (BlockedDestination, ValueError):
        return False
    return True


async def _on_request(request: httpx.Request) -> None:
    await check_request_url(str(request.url))


async def _on_response(response: httpx.Response) -> None:
    if response.has_redirect_location:
        await check_redirect(str(response.url), response.headers["location"])


def guard_hooks() -> Dict[str, list]:
    """``event_hooks`` for a direct httpx.AsyncClient. Hooks also run on each
    redirect hop, so followed redirects are covered."""
    return {"request": [_on_request], "response": [_on_response]}


def _vet_addresses(name: str, addresses: List[str]) -> None:
    classes = {classify_ip(address) for address in addresses}
    if METADATA in classes and not metadata_requests_allowed():
        raise BlockedDestination(f"Blocked connection: {name} resolves to a metadata address")
    if PRIVATE in classes and _was_recently_public(name):
        raise BlockedDestination(f"Blocked connection: {name} changed from public to private")


async def curl_pin(url: str) -> Optional[str]:
    """A libcurl RESOLVE entry fixing ``url``'s host to addresses that pass the rules,
    or None when there's nothing to pin: an IP literal, or a name that won't resolve."""
    parts = urlsplit(url)
    name = _normalize_host(parts.hostname)
    if not name:
        return None
    try:
        ipaddress.ip_address(name.split("%", 1)[0])
        return None
    except ValueError:
        pass
    loop = asyncio.get_running_loop()
    try:
        addresses = await asyncio.wait_for(loop.run_in_executor(None, _resolve, name), _RESOLVE_TIMEOUT)
    except (OSError, asyncio.TimeoutError):
        return None
    if not addresses:
        return None
    _vet_addresses(name, addresses)
    try:
        host = name.encode("idna").decode("ascii")
    except UnicodeError:
        host = name
    port = parts.port or (443 if parts.scheme == "https" else 80)
    literals = [f"[{a}]" if ":" in a else a for a in dict.fromkeys(addresses)]
    return f"{host}:{port}:{','.join(literals)}"


class _PinnedBackend(httpcore.AsyncNetworkBackend):
    """Resolves at connect time, re-applies the rules, and connects to the vetted
    address. TLS still validates and sends SNI for the original hostname."""

    def __init__(self) -> None:
        self._inner = httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        name = _normalize_host(host)
        if is_onion(name):
            raise BlockedDestination(f"Blocked direct connection to {name}: .onion addresses need Tor")
        try:
            ipaddress.ip_address(name.split("%", 1)[0])
            addresses = [name]
        except ValueError:
            if name in _METADATA_HOSTS and not metadata_requests_allowed():
                raise BlockedDestination(f"Blocked connection to a metadata address: {name}")
            try:
                addresses = await asyncio.get_running_loop().run_in_executor(None, _resolve, name)
            except OSError as exc:
                raise httpcore.ConnectError(f"Could not resolve {name}: {exc}") from exc

        _vet_addresses(name, addresses)

        last_error: Optional[Exception] = None
        for address in dict.fromkeys(addresses):
            try:
                return await self._inner.connect_tcp(
                    address, port, timeout=timeout, local_address=local_address,
                    socket_options=socket_options)
            except (httpcore.ConnectError, httpcore.ConnectTimeout) as exc:
                last_error = exc
        raise last_error or httpcore.ConnectError(f"No address for {name}")

    async def connect_unix_socket(self, path, timeout=None, socket_options=None):
        return await self._inner.connect_unix_socket(path, timeout=timeout, socket_options=socket_options)

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


def guarded_client(extra_request_hooks: Optional[list] = None, **kwargs) -> httpx.AsyncClient:
    """An httpx client for direct requests, with the guard applied."""
    extra = list(extra_request_hooks or [])
    if environment_proxy_active():
        return httpx.AsyncClient(event_hooks={"request": extra}, **kwargs)
    hooks = guard_hooks()
    hooks["request"] = hooks["request"] + extra
    client = httpx.AsyncClient(event_hooks=hooks, **kwargs)
    pool = getattr(client._transport, "_pool", None)
    if pool is not None:
        pool._network_backend = _PinnedBackend()
    return client
