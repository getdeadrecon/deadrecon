"""
DeadRecon Web Crawler — same-site crawl over the stealth client.

Every request goes through the shared stealth client, so the crawl inherits the
proxy pool, adaptive pacing, browser identity, attribution ledger and network
guard like any other module.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

from deadrecon.core.http import stealth_client
from deadrecon.core.netguard import BlockedDestination

logger = logging.getLogger("deadrecon.scrapers.crawler")

DEFAULT_MAX_PAGES = 200
MAX_PARSE_CHARS = 2_000_000
MAX_LINKS_PER_PAGE = 200
MAX_COMMENTS_PER_PAGE = 20

SKIPPED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "ico", "woff", "woff2", "ttf", "eot",
    "mp4", "mp3", "zip", "tar", "gz", "pdf", "webp", "css",
}
SECURITY_HEADERS = (
    "content-security-policy", "x-frame-options", "x-xss-protection",
    "x-content-type-options", "strict-transport-security", "referrer-policy",
    "permissions-policy",
)
SOCIAL_PLATFORMS = {
    "twitter.com": "twitter", "x.com": "twitter", "facebook.com": "facebook",
    "linkedin.com": "linkedin", "instagram.com": "instagram", "youtube.com": "youtube",
    "github.com": "github", "reddit.com": "reddit", "tiktok.com": "tiktok",
    "discord.com": "discord", "telegram.me": "telegram", "t.me": "telegram",
}
API_PATTERNS = (
    (r"/api/v?\d*/[\w/]+", "REST API path"),
    (r"/graphql", "GraphQL endpoint"),
    (r"swagger\.json|swagger\.yaml|openapi\.json", "OpenAPI spec"),
    (r"/\.well-known/[\w\-]+", "Well-known resource"),
    (r"api[_\-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})", "API key in source"),
    (r"authorization\s*[:=]\s*['\"]?Bearer\s+([A-Za-z0-9_\-\.]+)", "Bearer token"),
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\b\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")


class _PageParser(HTMLParser):
    """Collects what the crawl reports. Tolerates malformed HTML, as targets may
    serve anything."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.links: List[str] = []
        self.scripts: List[str] = []
        self.forms: List[Dict[str, Any]] = []
        self.meta: Dict[str, str] = {}
        self.comments: List[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {key: (value or "") for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        elif tag == "form":
            self.forms.append({"action": a.get("action", ""),
                               "method": a.get("method", "get").upper(), "inputs": []})
        elif tag in ("input", "textarea", "select") and self.forms:
            self.forms[-1]["inputs"].append({"name": a.get("name", ""),
                                             "type": a.get("type", "text"),
                                             "id": a.get("id", "")})
        elif tag == "meta":
            name = a.get("name") or a.get("property")
            if name and a.get("content"):
                self.meta[name] = a["content"]

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and not self.title:
            self.title = data.strip()

    def handle_comment(self, data: str) -> None:
        text = data.strip()
        if len(text) > 3 and len(self.comments) < MAX_COMMENTS_PER_PAGE:
            self.comments.append(text)


def _security_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    present = {name: headers[name] for name in SECURITY_HEADERS if headers.get(name)}
    missing = [name for name in SECURITY_HEADERS if name not in present]
    return {"present": present, "missing": missing,
            "score": int(len(present) / len(SECURITY_HEADERS) * 100)}


def analyze_page(url: str, status: int, headers: Dict[str, str], body: str) -> Dict[str, Any]:
    """Turn one fetched page into a ``web_page`` record. Pure, for easy testing."""
    text = body[:MAX_PARSE_CHARS]
    parser = _PageParser()
    try:
        parser.feed(text)
    except Exception as exc:  # a hostile page must not end the crawl
        logger.debug("HTML parse stopped early on %s: %s", url, exc)
    links = list(dict.fromkeys(urljoin(url, href) for href in parser.links))[:MAX_LINKS_PER_PAGE]
    social: Dict[str, str] = {}
    for link in parser.links:
        host = (urlparse(link).hostname or "").lower()
        for domain, name in SOCIAL_PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                social[name] = link
    hints = [{"type": label, "value": match}
             for pattern, label in API_PATTERNS
             for match in re.findall(pattern, text, re.IGNORECASE)]
    lowered = {key.lower(): value for key, value in headers.items()}
    return {
        "type": "web_page",
        "url": url,
        "status_code": status,
        "content_type": lowered.get("content-type", ""),
        "title": parser.title,
        "description": parser.meta.get("description", ""),
        "headers": lowered,
        "links": links,
        "forms": parser.forms,
        "emails": sorted(set(EMAIL_RE.findall(text))),
        "phone_numbers": sorted(set(PHONE_RE.findall(text))),
        "api_hints": hints,
        "js_files": [urljoin(url, src) for src in parser.scripts],
        "comments": parser.comments,
        "meta_tags": parser.meta,
        "social_links": social,
        "security_headers": _security_headers(lowered),
    }


def _crawlable(url: str, netloc: str) -> bool:
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or parts.netloc != netloc:
        return False
    extension = parts.path.rsplit(".", 1)[-1].lower() if "." in parts.path.rsplit("/", 1)[-1] else ""
    return extension not in SKIPPED_EXTENSIONS


class WebCrawler:
    """Breadth-first crawl of one site, bounded by depth and page count."""

    def __init__(self, config):
        self.config = config

    async def _load_robots(self, client, start_url: str) -> Optional[RobotFileParser]:
        if not self.config.get("scraper", "respect_robots_txt", default=True):
            return None
        robots = RobotFileParser()
        try:
            response = await client.get(urljoin(start_url, "/robots.txt"))
        except Exception as exc:
            logger.debug("robots.txt unavailable: %s", exc)
            return None
        if response.status_code != 200:
            return None
        robots.parse(response.text[:MAX_PARSE_CHARS].splitlines())
        return robots

    async def crawl(self, target: str, depth: int = 2, options: Optional[dict] = None) -> List[Dict]:
        options = options or {}
        start = target if target.startswith(("http://", "https://")) else f"https://{target}"
        start = urldefrag(start)[0]
        netloc = urlparse(start).netloc
        max_pages = int(options.get("max_pages") or self.config.get(
            "scraper", "max_pages", default=DEFAULT_MAX_PAGES))

        results: List[Dict] = []
        seen: Set[str] = {start}
        frontier: List[Tuple[str, int]] = [(start, 0)]

        async with stealth_client(self.config, follow_redirects=True, timeout=30) as client:
            robots = await self._load_robots(client, start)
            user_agent = "*"
            while frontier and len(results) < max_pages:
                url, level = frontier.pop(0)
                if robots is not None and not robots.can_fetch(user_agent, url):
                    continue
                try:
                    response = await client.get(url)
                except BlockedDestination as exc:
                    logger.warning("Crawl skipped %s: %s", url, exc)
                    continue
                except Exception as exc:
                    logger.debug("Crawl fetch failed for %s: %s", url, exc)
                    continue

                final_url = str(response.url)
                if urlparse(final_url).netloc != netloc:
                    continue  # redirected off-site: out of scope
                page = analyze_page(final_url, response.status_code, dict(response.headers), response.text)
                results.append({
                    "type": "web_page",
                    "source": "web_crawler",
                    "data": page,
                    "confidence": 1.0,
                    "relevance_score": 0.8,
                    "tags": ["web", "crawl"],
                })
                if level >= depth:
                    continue
                for link in page["links"]:
                    candidate = urldefrag(link)[0]
                    if candidate not in seen and _crawlable(candidate, netloc):
                        seen.add(candidate)
                        frontier.append((candidate, level + 1))
        return results
