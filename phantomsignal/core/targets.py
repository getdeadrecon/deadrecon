"""
PhantomSignal scan-target validation.

Scans can start from a form, the REST API or the CLI, and a target eventually
reaches external tools as an argument. Rejecting malformed input at the door
keeps flag-like or control-character values out of that path.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

MAX_TARGET_LENGTH = 2048
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s")
PEOPLE_SCAN_TYPES = {"people_intel"}


class InvalidTarget(ValueError):
    """The message is safe to show to the user."""


def validate_target(value, scan_type: str = "web_recon") -> str:
    """Return the cleaned target, or raise InvalidTarget. Private and internal
    addresses are allowed, because scanning them is a legitimate operator choice."""
    target = str(value or "").strip()
    if not target:
        raise InvalidTarget("Target is required.")
    if len(target) > MAX_TARGET_LENGTH:
        raise InvalidTarget(f"Target must be {MAX_TARGET_LENGTH} characters or fewer.")
    if _CONTROL_CHARS.search(target):
        raise InvalidTarget("Target contains control characters.")
    if target.startswith("-"):
        raise InvalidTarget("Target can't start with a hyphen.")
    if str(scan_type) in PEOPLE_SCAN_TYPES:
        return target  # people searches can legitimately contain spaces
    if _WHITESPACE.search(target):
        raise InvalidTarget("Target can't contain spaces.")
    if "://" in target:
        try:
            parts = urlsplit(target)
        except ValueError:
            raise InvalidTarget("Target URL is malformed.")
        if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
            raise InvalidTarget("Target URLs must use http or https.")
    return target
