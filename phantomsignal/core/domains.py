"""
Registered-domain parsing that never touches the network.

tldextract's default downloads the public suffix list on first use, directly from
the operator's IP. Using its bundled snapshot keeps parsing offline.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import tldextract

extract = tldextract.TLDExtract(suffix_list_urls=())
