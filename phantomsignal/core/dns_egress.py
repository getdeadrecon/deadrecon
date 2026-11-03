"""
PhantomSignal DNS egress — keeps DNS lookups from bypassing the proxy.

A proxy hides an operator's IP from a target, but a lookup sent to the system
resolver still tells that resolver every name being investigated. When a proxy is
configured, lookups go over DNS-over-HTTPS (RFC 8484) through the proxy instead,
and fail rather than falling back to the system resolver. With no proxy configured
the system resolver is used as normal.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import logging
import random
import threading
from typing import Dict, List, Optional

import dns.message
import dns.name
import dns.rcode
import dns.rdatatype
import dns.resolver
import dns.reversename
import httpx

logger = logging.getLogger("phantomsignal.dns_egress")

DEFAULT_DOH_URL = "https://cloudflare-dns.com/dns-query"
_MAX_ATTEMPTS = 3
_MAX_RESPONSE_BYTES = 65535


def configured_proxies(config) -> List[str]:
    """The real proxies in the egress config. Direct (``None``) entries don't count."""
    from phantomsignal.core.http import resolve_egress
    egress, _ = resolve_egress(config)
    return [proxy for proxy in egress if proxy]


class ProxiedResolver:
    """A drop-in for the parts of ``dns.resolver.Resolver`` this project uses.
    Returns real dnspython rdata objects, and is safe to call from worker threads."""

    def __init__(self, proxies: List[str], doh_url: str = DEFAULT_DOH_URL, min_lifetime: float = 0.0):
        self._proxies = list(proxies)
        self._min_lifetime = min_lifetime
        self._doh_url = doh_url
        self._clients: Dict[str, httpx.Client] = {}
        self._lock = threading.Lock()
        self.timeout = 5.0
        self.lifetime = 8.0

    @property
    def lifetime(self) -> float:
        return self._lifetime

    @lifetime.setter
    def lifetime(self, value: float) -> None:  # callers tune this for direct DNS speeds
        self._lifetime = max(value, self._min_lifetime)

    def _client(self, proxy: str) -> httpx.Client:
        with self._lock:
            client = self._clients.get(proxy)
            if client is None:
                client = httpx.Client(proxy=proxy, verify=True, timeout=self.lifetime)
                self._clients[proxy] = client
            return client

    def _exchange(self, query: dns.message.Message) -> dns.message.Message:
        last_error: Optional[Exception] = None
        order = random.sample(self._proxies, len(self._proxies))
        for proxy in order[:_MAX_ATTEMPTS]:
            try:
                response = self._client(proxy).post(
                    self._doh_url, content=query.to_wire(),
                    headers={"content-type": "application/dns-message",
                             "accept": "application/dns-message"})
                response.raise_for_status()
                if len(response.content) > _MAX_RESPONSE_BYTES:
                    raise ValueError("DNS response too large")
                return dns.message.from_wire(response.content)
            except Exception as exc:
                last_error = exc
                logger.debug("DoH lookup failed: %s", exc)
        # Never fall back to the system resolver: that's the leak this class prevents.
        raise dns.resolver.NoNameservers(f"DoH lookup failed through every proxy tried: {last_error}")

    def resolve(self, qname, rdtype="A", *args, **kwargs) -> List:
        name = qname if isinstance(qname, dns.name.Name) else dns.name.from_text(str(qname))
        if name.to_text().lower().rstrip(".").endswith(".onion"):  # RFC 7686: never in DNS
            raise dns.resolver.NXDOMAIN(qnames=[name])
        wanted = dns.rdatatype.from_text(rdtype) if isinstance(rdtype, str) else rdtype
        reply = self._exchange(dns.message.make_query(name, wanted))
        if reply.rcode() == dns.rcode.NXDOMAIN:
            raise dns.resolver.NXDOMAIN(qnames=[name])
        if reply.rcode() != dns.rcode.NOERROR:
            raise dns.resolver.NoNameservers(f"DoH answered {dns.rcode.to_text(reply.rcode())}")
        answers = [rdata for rrset in reply.answer if rrset.rdtype == wanted for rdata in rrset]
        if not answers:
            raise dns.resolver.NoAnswer(f"No {dns.rdatatype.to_text(wanted)} records for {name}")
        return answers


def make_resolver(config):
    """A resolver that respects the configured egress."""
    proxies = configured_proxies(config)
    if proxies:
        from phantomsignal.core.tor import MIN_TIMEOUT, tor_enabled
        return ProxiedResolver(proxies, config.get("scraper", "doh_url", default=DEFAULT_DOH_URL),
                               min_lifetime=MIN_TIMEOUT if tor_enabled(config) else 0.0)
    return dns.resolver.Resolver()


def lookup_ptr(resolver, ip: str) -> Optional[str]:
    try:
        return str(resolver.resolve(dns.reversename.from_address(ip), "PTR")[0]).rstrip(".")
    except Exception:
        return None
