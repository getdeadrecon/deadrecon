<p align="center"><img src="https://raw.githubusercontent.com/getdeadrecon/deadrecon/main/docs/assets/deadrecon-card.png" width="276" alt="DeadRecon logo: tarot card XIII, a skull with a red censor bar across its eyes"></p>

# DeadRecon

*Formerly PhantomSignal.*

> **The OPSEC-native OSINT framework** — _"Map the surface. Own the signal."_
>
> Recon that doesn't burn your infrastructure — a shared stealth egress layer, one-click
> Tor, and an honest per-scan report of exactly what you leaked.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-ff3b1f?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-f7de52?style=flat-square)](https://github.com/getdeadrecon/deadrecon/blob/main/LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Docker-111111?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/getdeadrecon/deadrecon?style=flat-square&color=ff3b1f)](https://github.com/getdeadrecon/deadrecon/stargazers)
[![Open Issues](https://img.shields.io/github/issues/getdeadrecon/deadrecon?style=flat-square&color=111111)](https://github.com/getdeadrecon/deadrecon/issues)
[![CI](https://img.shields.io/github/actions/workflow/status/getdeadrecon/deadrecon/ci.yml?branch=main&style=flat-square&label=CI&color=ff3b1f)](https://github.com/getdeadrecon/deadrecon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/deadrecon?style=flat-square&color=111111&logo=pypi&logoColor=white)](https://pypi.org/project/deadrecon/)
[![Project Site](https://img.shields.io/badge/site-deadrecon.sh-f7de52?style=flat-square&logo=github)](https://deadrecon.sh)
[![Changelog](https://img.shields.io/badge/changelog-view-ff3b1f?style=flat-square)](https://github.com/getdeadrecon/deadrecon/blob/main/CHANGELOG.md)


---

## ⚡ What's New in v1.31 — New look, and a quieter console

- **The console contacts no other servers by default.** It used to load from Google Fonts, cdnjs and
  unpkg, which told them you were using it. Those files now ship with the package. A map tile server
  you configure is still contacted.
- **A new look:** black, signal red and a new logo. The Light theme is gone.
- **Fixes:** exports no longer crash on a scan with no score, maps stay dark without a basemap, and
  PDF reports print cleanly.

---

## ⚡ What's New in v1.30 — PhantomSignal is now DeadRecon

Same tool, new name. **Nothing you've saved is lost.**

- **On first run**, `~/.phantomsignal` moves to `~/.deadrecon`, and a `phantomsignal.db` moves
  to `deadrecon.db`. Your API keys, scans and account come with them. You'll need to log in again.
- **Old settings still work:** `PHANTOMSIGNAL_*` variables and the `phantomsignal` and `psig` commands.
- **Scans no longer name the tool** to targets or third parties. That includes SMTP greetings and
  User-Agents, and it was checked against packet captures.
- **Upgrading with pip:** run `pip uninstall phantomsignal` first, then `pip install deadrecon`. In the
  other order, the uninstall removes the old commands.
- **Upgrading with Docker:** run `docker-compose down` *before* you pull, or the old container keeps
  port 5000. Your data volumes keep their names, so your data stays.

---

## ⚡ What's New in v1.29 — One-click Tor + honest OPSEC grades

**If you used Tor before 1.29.0, those scans were not on Tor.** The old setting and the
`--profile covert` container never routed scan traffic, so they connected directly.

- **One-click Tor** — click 🧅 and DeadRecon starts Tor for you, with nothing to
  install or configure. Add `--tor` on the CLI. Tor is built into the Docker image.
- **Fails closed** — each scan confirms it's on Tor before touching the target and stops
  if it can't. Modules that would bypass Tor are skipped and listed in the report.
- **Grades checked against packet captures** — all module HTTP is counted, DNS goes
  through the proxy, and a module that sends a direct request is reported as attributable.
- **`nuclei` is reported as attributable even with a proxy** — some of its traffic still
  connects directly, so don't rely on a proxy to hide `nuclei` scans.
- **Security hardening** — SSRF and DNS rebinding protection, a nonce-based CSP, safe XML
  parsing, and a non-root Docker image with dependencies pinned by hash.
- **Protection from hostile targets (1.29.3)** — crafted pages can't stall JS mining, downloads
  stop at 3 MB, and public pages can't send script or favicon fetches to private addresses.
  Telegram bot tokens stay out of results and logs, so if you've used a Telegram key, check saved
  scans, exports and logs, and rotate the token if it appears.
- **Console login (since 1.28.0)** — the web console needs an operator account, and REST
  calls need `Authorization: Bearer <token>`. The first run prints a setup token.

**Upgrading from Docker?** The container no longer runs as root, so there's a one-time
`chown`. See the [changelog](https://github.com/getdeadrecon/deadrecon/blob/main/CHANGELOG.md).

**Limits:** the Windows and Intel Mac Tor bundles haven't been run, and automatic Tor
start doesn't set up bridges, so networks that block Tor need a self-run Tor service.

---

## ⚡ What's New in v1.27.0 — Identity intelligence + egress you can see

**The Profiler grew up.** Eight new **keyless** public sources feed it, every
run is now saved as a scan you can revisit and export, and the whole stealth
posture is visible in the navbar and survives a restart.

- **8 no-key identity sources** — XposedOrNot (breach exposure with no HIBP key),
  a GitHub commit-email harvester (real name + email from public commits),
  GitLab, Wikidata (DOB + cross-linked socials for named people), WebFinger
  (fediverse resolution), **offline phone intel** via libphonenumber (zero
  network egress), openFEC (US employer/occupation), and OpenCorporates.
- **Profiler → Scans** — a Profiler search now persists as a `people_intel` scan
  (with a linked shadow profile), so it lands in **Scans** with history,
  summary, and export. A **View in Scans** button jumps straight there.
- **Egress routed + graded** — the keyless sources inherit the shared proxy pool
  and land in the attribution ledger. A **STEALTH / PARTIAL / DIRECT** chip in
  the navbar shows your live posture at a glance.
- **Proxy pools in one click** — seed the rotating pool from curated free feeds,
  a custom URL, or an uploaded list, right from Scan Settings.
- **Settings persist** — stealth profile, proxy pool, rotation, and the rest now
  survive a restart.

See the [CHANGELOG](https://github.com/getdeadrecon/deadrecon/blob/main/CHANGELOG.md) for the full list.

---

## ⚡ What's New in v1.26.0 — Best-of-breed engines + the vuln loop

**DeadRecon now closes the ASM loop and runs fast Go-native engines — under
stealth governance.** It maps the surface *and* flags what's exploitable, and
orchestrates the best external tools when installed, and reports it honestly when
one can't be masked.

### 🎯 Vulnerability scanning (nuclei)
The new `vuln_scan` module wraps **nuclei**, emitting `vulnerability` findings
with normalised severity into the Findings & Exposure view, and exporting them as
**STIX 2.1 Vulnerability SDOs**. Active and loud, so it's strictly opt-in — never
part of the default sweep.

### ⚡ Speed adapters, native fallback preserved
Optional Go-native engines join the pipeline when installed and fall back to the
pure-Python modules when not — a binary-free `pip install` keeps working:

| Module | Tool | Posture | Fallback |
|--------|------|---------|----------|
| `subdomain_enum_fast` | subfinder | proxied | native enumerator |
| `port_scan_fast` | naabu | attributable (raw socket) | native scanner |
| `web_crawl_fast` | katana | proxied (with a proxy) | native crawler |
| `tls_fingerprint` | tlsx | attributable | complements infra_pivot |

Every adapter inherits the shared proxy egress where the tool supports it, and is
tagged honestly in the attribution report — a raw-socket scanner is never
labelled "masked."

---

## ⚡ Also new — OPSEC Core (v1.25.0)

**DeadRecon reports its own attribution surface.** No other open-source
OSINT framework tells you what a scan leaked about *you*.

### 🛰 Attribution Surface — "what did this scan leak?"
Every scan ends with an honest OPSEC grade — **masked**, **partial**, **exposed**,
or **quiet** — computed from real egress telemetry, not marketing:

- **% proxied vs. direct** — how many requests left through the proxy pool vs.
  straight from your IP.
- **JA3/JA4 profiles presented** — which browser TLS fingerprints you wore, and
  how often.
- **WAF challenges & adaptive backoffs** — where a defence noticed you.
- **Per-module OPSEC breakdown** — every module tagged `stealth-guaranteed`,
  `proxied`, or `attributable`, so you see which parts of a run are masked and
  which are traceable back to you.

The grade is deliberately unflattering: any attributable module, or under-50%
proxied traffic, caps it, and no scan can read as masked or quiet without a proxy.
**Masked** takes stealth-level modules only, no direct requests, and TLS impersonation
on nearly every request, so a port scan or a Go tool in the run rules it out. The point of an OPSEC-native tool is to tell you the
truth about your footprint — not to always read green.

Under Tor, Partial doesn't mean traffic went direct. Tor scans skip modules that would
bypass it, and a scan grades Partial when some requests didn't wear a browser TLS
fingerprint. The report says when that's the reason.

### 🧅 Shared stealth layer
The shared stealth client (proxy pool + per-host adaptive pacing + sticky browser
identity + optional JA3/JA4 impersonation) is now the spine. Target-facing
document downloads route through it too — no more scanner User-Agent hitting the
target directly.

### 🧩 Module registry
A `@register_module` plugin registry (mirroring the intel-API pattern) replaces
the engine's hard-coded module table — new recon modules join the pipeline by
registering, and declare their OPSEC posture up front.

---

## 🎬 A Scan in Action

A single command runs the full pipeline — DNS and WHOIS resolution, port and
service scanning, technology fingerprinting, threat-intelligence correlation
across 50+ sources, and a web-surface crawl — then rolls every finding into a
single Risk Score and writes a shareable HTML report.

```text
$ deadrecon scan example.com --profile standard --opsec quiet --format html

◈  Target   : example.com  (domain)
◈  Profile  : standard     (~2–5 min)
◈  OPSEC    : quiet        (proxy pool · adaptive pacing · JA3)
◈  Modules  : dns_recon port_scan tech_detect api_hunt web_crawl intel

[1/6] DNS & WHOIS ......... 42 records · 7 subdomains
[2/6] Port scan .......... 6 open · 22 80 443 8080 …
[3/6] Tech fingerprint ... nginx · Cloudflare · React · WordPress
[4/6] Threat intel ....... 31 sources queried · 0 malicious
[5/6] Web crawl .......... 128 URLs · 3 exposed endpoints
[6/6] Scoring ............ Risk Score 34 / 100 (MEDIUM)

◈  OPSEC ............. EXPOSED · 100% of HTTP proxied · attributable: port_scan, intel
✓  Report written → ./reports/example.com.html
```

This output is illustrative. By default the CLI runs `dns_recon`, `port_scan`,
`tech_detect`, `api_hunt` and `intel`; add others with `--modules`.

Stages run concurrently where possible and degrade gracefully — a module
without a configured API key returns empty rather than failing the scan.

## ⚡ What is DeadRecon?

DeadRecon is a **community-powered, open-source OSINT intelligence framework** built for security researchers, penetration testers, investigators, and enthusiasts. It combines web scraping, network reconnaissance, people intelligence aggregation, and threat analysis into a single cohesive platform.

> **LEGAL DISCLAIMER:** DeadRecon is for **authorized security research, OSINT investigations, and educational purposes only**. Only scan targets you have explicit permission to test. You are solely responsible for compliance with all applicable laws. The developers assume NO liability for misuse.

---

## 🔥 Features

### 🕷 Web Reconnaissance
- **Same-site web crawler** that runs through the stealth layer, honoring proxies and robots.txt
- **Technology detection** — fingerprints 50+ technologies (CMS, frameworks, CDNs, WAFs)
- **API endpoint hunter** — discovers REST APIs, GraphQL, Swagger docs, admin panels, `.env` leaks
- **Security header analysis** with graded posture scoring
- **Email, phone, link, and comment harvesting**

### 🌐 Network Intelligence
- **nmap-powered port scanner** — full service-version detection and OS fingerprinting via nmap (`-sV -O`); pure-Python async TCP fallback when nmap unavailable — no config required
- **Expanded port coverage** — 99 common ports by default, 1,000+ port profile, or full 65,535; covers WinRM, Webmin, InfluxDB, Docker API, Kubernetes, and more
- **DNS recon** — A/AAAA/MX/NS/TXT/SOA/CAA, zone transfer attempts, subdomain brute-force
- **Certificate transparency** via crt.sh — uncover subdomains via SSL history
- **SPF/DMARC analysis** — identify email spoofing vulnerabilities
- **Reverse DNS** and co-hosted domain discovery

### 🔬 Intelligence APIs (50+ Integrations)

| Category | APIs |
|----------|------|
| **Network Scanning** | Shodan, Censys, ZoomEye, BinaryEdge |
| **Threat Intelligence** | VirusTotal, AbuseIPDB, GreyNoise, AlienVault OTX, Intelligence X |
| **Email & Breach** | Hunter.io, HaveIBeenPwned, EmailRep, **XposedOrNot** (no key) |
| **Domain/Web** | SecurityTrails, URLScan.io, WhoisXML, Local WHOIS |
| **Geolocation** | IPInfo.io |
| **Phone** | Abstract API, **offline libphonenumber metadata** (no key, zero egress) |
| **People Search** | Pipl, FullContact, WhitePages, Spokeo, Clearbit, **Wikidata** · **openFEC** · **OpenCorporates** (all no key) |
| **Social** | GitHub, GitHub commit-email harvester, **GitLab**, **WebFinger**, Twitter/X, Reddit, Mastodon, Keybase, Gravatar, HackerNews, Twitch, YouTube, Instagram, TikTok, LinkedIn, Tumblr, Flickr, Spotify, Steam, VK, Telegram, Discord, Facebook |
| **Custom** | Bring your own API via plugin architecture |

> **No-key head start** — a whole tier of the Profiler works with **zero API
> keys**: XposedOrNot (breaches), the GitHub commit-email harvester, GitLab,
> Wikidata, WebFinger, offline phone metadata, openFEC, and OpenCorporates —
> plus the existing GitHub/Reddit/Mastodon/Keybase/Gravatar/HackerNews sources.
>
> **What gets proxied:** a set of keyless identity sources use your proxy. Other API
> sources, including keyed providers, connect directly unless Tor is on, and the `intel`
> module is reported as attributable. Under Tor, all of them use Tor.

### 👤 Profiler (People Intelligence)
LexisNexis-style identity aggregation from public records:
- Cross-correlates data from multiple people-search APIs — **many keyless**
- Discovers emails, phones, addresses, relatives, employers
- Breach correlation via **XposedOrNot (no key)**, HIBP, and Intelligence X
- Real name + email harvested from public GitHub/GitLab commits
- Social media profile linking; fediverse resolution via WebFinger
- **Risk Score** — digital exposure quantification (0-100)
- **Every run is saved as a scan** — persisted as a `people_intel` scan with a
  linked shadow profile, so it shows up under **Scans** with history, summary,
  and export (with a **View in Scans** shortcut from the results page)

### 📦 Export Formats
| Format | Description |
|--------|-------------|
| **JSON** | Raw machine-readable data |
| **CSV** | Spreadsheet-compatible |
| **HTML** | Self-contained styled report |
| **PDF** | Professional dossier via ReportLab |
| **XML** | Structured data |
| **XLSX** | Excel workbook |
| **STIX 2.1** | Threat intelligence sharing format |
| **Markdown** | Human-readable report |

All formats support **ZIP compression** and **AES-256-GCM encryption**.

### 🌑 Covert Recon
- Low-and-slow **Covert** scan profile to minimize noise
- **Stealth profiles** (`off` / `quiet` / `paranoid`) — per-host adaptive pacing,
  sticky browser identity, JA3/JA4 impersonation, and WAF-aware backoff
- **Rotating proxy pool** with sticky/per-request rotation and auto-benching of
  burned egresses — **seed it in one click** from curated free feeds, a custom
  list URL, or an uploaded file (Settings → Scan Settings)
- **Live egress posture chip** in the navbar — STEALTH / PARTIAL / DIRECT at a glance
- **One-click Tor:** click the 🧅 button and DeadRecon starts Tor for you, with nothing to install or configure. Each scan confirms it's on Tor before touching the target, targets get separate circuits, `.onion` targets work, and modules that would bypass Tor are skipped and reported
- Configurable request jitter and delays, toggled via **Evasive** mode
- **Egress settings persist** across restarts

### 🔔 Additional Features
- **Real-time live feed** — WebSocket-powered terminal during scans
- **Risk Score** — composite risk/exposure scoring
- **Scheduled Scans** — recurring automated scans
- **API health monitor** — dashboard showing configured APIs and rate limits
- **Full REST API** — integrate DeadRecon into your own toolchain
- **CLI interface** — `deadrecon scan`, `deadrecon profile`, `deadrecon export`
- **Docker** — single-command deployment

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
git clone https://github.com/getdeadrecon/deadrecon
cd deadrecon
docker-compose up -d
docker logs deadrecon   # copy the first-run setup token
# Open http://localhost:5000 and create your operator account

# Optional: include nuclei, katana, subfinder, naabu and tlsx (about 500 MB more)
DEADRECON_RECON_TOOLS=true docker-compose up -d --build
```

### Option 2: Manual Installation
```bash
# Python 3.10+ required
git clone https://github.com/getdeadrecon/deadrecon
cd deadrecon
pip install -e .
deadrecon init
deadrecon web --open-browser
# The first run prints a setup token in this terminal; use it to create your account
```

### Option 3: CLI Scan
```bash
# Quick scan
deadrecon scan example.com --profile quick

# Over Tor: starts Tor for you, and stops if it can't confirm it
deadrecon scan example.com --tor

# IP recon with an HTML report
deadrecon scan 192.168.1.1 --type ip_recon --format html --output ./reports

# People intelligence
deadrecon profile --email target@company.com --first-name John --last-name Doe
```

---

## ⚙️ Configuration

### Environment Variables (Recommended for API Keys)
```bash
export SHODAN_API_KEY="your-shodan-key"
export VIRUSTOTAL_API_KEY="your-vt-key"
export HUNTER_API_KEY="your-hunter-key"
export HIBP_API_KEY="your-hibp-key"
export GREYNOISE_API_KEY="your-greynoise-key"
export IPINFO_TOKEN="your-ipinfo-token"
export ABUSEIPDB_API_KEY="your-abuseipdb-key"
export ALIENVAULT_API_KEY="your-otx-key"
export GITHUB_TOKEN="your-github-token"
export SECURITYTRAILS_API_KEY="your-st-key"
```

### Config File
Settings are saved to `~/.deadrecon/config.yaml` (owner-only). Most can be changed
from the web console.

### Egress / stealth (Settings → Scan Settings)
Set your stealth profile, single proxy, and rotating proxy pool from the web UI.
Seed the pool from curated free proxy feeds, a custom list URL, or an uploaded
file. These egress settings are **saved to `~/.deadrecon/config.yaml` and
persist across restarts** (env-provided API keys are never copied there). Free
public proxies are unvetted — treat them as blend-in cover for low-sensitivity
recon, pair with HTTPS, and prefer your own egress for anything sensitive.

---

## 🔌 Adding Custom APIs

DeadRecon uses a plugin architecture. Adding a new intelligence source takes ~20 lines:

```python
# deadrecon/intel/apis/my_api.py
from deadrecon.intel.apis.base import BaseIntelAPI, register_api, APICategory, APITier

@register_api
class MyAPI(BaseIntelAPI):
    NAME = "myapi"
    DESCRIPTION = "My custom intelligence source"
    REQUIRES_KEY = True
    TIER = APITier.FREE_LIMITED
    CATEGORIES = [APICategory.NETWORK]
    BASE_URL = "https://api.myservice.com/v1"
    SIGN_UP_URL = "https://myservice.com/signup"

    async def search(self, query: str, **kwargs):
        data = await self._get(
            f"{self.BASE_URL}/search",
            params={"q": query, "key": self._api_key}
        )
        return [self._wrap_result("my_result", data)]
```

Then import it in `deadrecon/intel/orchestrator.py` and it auto-registers.

---

## 🏗 Architecture

```
deadrecon/
├── core/               — Engine, config, database, models
├── scrapers/           — Web crawler, tech detector, port scanner, API hunter, DNS recon
├── intel/
│   ├── apis/           — 50+ API integrations (plugin architecture; incl. keyless identity sources)
│   └── people/         — People intelligence aggregation + Profiler→scan persistence
├── exporters/          — JSON/CSV/PDF/HTML/XML/XLSX/STIX + crypto wrapper
└── web/
    ├── routes/         — Flask blueprints (dashboard, scans, intel, settings, export, REST API)
    ├── templates/      — Jinja2 templates
    └── static/         — CSS (role tokens), JS (terminal, app)
```

---

## 🛡 REST API

Every endpoint except the health check needs a token. Create one with
`deadrecon api-token` (this revokes the previous token).

```bash
export PSIG_TOKEN=psig_...

# Create a scan
curl -X POST http://localhost:5000/api/v1/scans \
  -H "Authorization: Bearer $PSIG_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "scan_type": "web_recon"}'

# Get results
curl -H "Authorization: Bearer $PSIG_TOKEN" http://localhost:5000/api/v1/scans/{scan_id}

# List all APIs
curl -H "Authorization: Bearer $PSIG_TOKEN" http://localhost:5000/api/v1/apis

# Health check (no token needed)
curl http://localhost:5000/api/v1/health
```

---

## 🤝 Contributing

DeadRecon thrives on community contributions. Ways to help:

1. **Add API integrations** — Follow the plugin pattern above
2. **Improve detection signatures** — Expand `tech_detector.py`
3. **Bug reports** — [GitHub Issues](https://github.com/getdeadrecon/deadrecon/issues)
4. **Documentation** — Improve the wiki
5. **Translations** — Internationalize the UI

See [CONTRIBUTING.md](https://github.com/getdeadrecon/deadrecon/blob/main/CONTRIBUTING.md) for guidelines. Please also review our [Code of Conduct](https://github.com/getdeadrecon/deadrecon/blob/main/CODE_OF_CONDUCT.md) and [Security Policy](https://github.com/getdeadrecon/deadrecon/blob/main/SECURITY.md).

---

## 📖 Documentation

- **[Usage Guide](https://github.com/getdeadrecon/deadrecon/blob/main/docs/USAGE.md)** — full walkthroughs, usage scenarios, CLI reference, and per-platform troubleshooting (Linux / macOS / Windows / Docker)
- **[Locate Guide](https://github.com/getdeadrecon/deadrecon/blob/main/docs/LOCATE.md)** — person geographic-footprint investigations: cases, signal capture (incl. EXIF from a photo URL), confidence model, pattern-of-life, handoff export, and chain of custody
- **[Releasing](https://github.com/getdeadrecon/deadrecon/blob/main/docs/RELEASING.md)** — how a release is cut (version bump → tag → GitHub Release) and the PyPI token setup

---

## ⚠️ Legal & Ethics

DeadRecon is a dual-use tool. Operators are responsible for:
- Obtaining explicit authorization before scanning any system
- Complying with applicable laws (CFAA, GDPR, CCPA, ECPA, local laws)
- Respecting privacy and data protection regulations
- Not using this tool for harassment, stalking, or unauthorized surveillance

**The developers provide this software as-is with no warranty. Misuse is your responsibility.**

This software is intended for authorized security research, OSINT investigation, and educational
purposes only. Users are solely responsible for ensuring their use complies with all applicable
local, state, national, and international laws. The authors assume no liability for misuse or
damage caused by this software.

---

## 🏷 Topics

[![osint](https://img.shields.io/badge/osint-ff3b1f?style=flat-square)](https://github.com/topics/osint)
[![security](https://img.shields.io/badge/security-f7de52?style=flat-square)](https://github.com/topics/security)
[![python](https://img.shields.io/badge/python-f7de52?style=flat-square)](https://github.com/topics/python)
[![hacking](https://img.shields.io/badge/hacking-ff3b1f?style=flat-square)](https://github.com/topics/hacking)
[![cybersecurity](https://img.shields.io/badge/cybersecurity-111111?style=flat-square)](https://github.com/topics/cybersecurity)
[![reconnaissance](https://img.shields.io/badge/reconnaissance-ff3b1f?style=flat-square)](https://github.com/topics/reconnaissance)
[![recon](https://img.shields.io/badge/recon-f7de52?style=flat-square)](https://github.com/topics/recon)
[![penetration-testing](https://img.shields.io/badge/penetration--testing-111111?style=flat-square)](https://github.com/topics/penetration-testing)
[![ethical-hacking](https://img.shields.io/badge/ethical--hacking-ff3b1f?style=flat-square)](https://github.com/topics/ethical-hacking)
[![bug-bounty](https://img.shields.io/badge/bug--bounty-f7de52?style=flat-square)](https://github.com/topics/bug-bounty)
[![information-gathering](https://img.shields.io/badge/information--gathering-111111?style=flat-square)](https://github.com/topics/information-gathering)
[![threat-intelligence](https://img.shields.io/badge/threat--intelligence-ff3b1f?style=flat-square)](https://github.com/topics/threat-intelligence)
[![security-tools](https://img.shields.io/badge/security--tools-f7de52?style=flat-square)](https://github.com/topics/security-tools)
[![network-scanner](https://img.shields.io/badge/network--scanner-111111?style=flat-square)](https://github.com/topics/network-scanner)
[![dns-recon](https://img.shields.io/badge/dns--recon-ff3b1f?style=flat-square)](https://github.com/topics/dns-recon)
[![infosec](https://img.shields.io/badge/infosec-f7de52?style=flat-square)](https://github.com/topics/infosec)
[![flask](https://img.shields.io/badge/flask-111111?style=flat-square)](https://github.com/topics/flask)
[![security-research](https://img.shields.io/badge/security--research-ff3b1f?style=flat-square)](https://github.com/topics/security-research)
[![footprinting](https://img.shields.io/badge/footprinting-f7de52?style=flat-square)](https://github.com/topics/footprinting)
[![automation](https://img.shields.io/badge/automation-111111?style=flat-square)](https://github.com/topics/automation)

---

## 🤝 Community

| Document | Description |
|----------|-------------|
| [Code of Conduct](https://github.com/getdeadrecon/deadrecon/blob/main/CODE_OF_CONDUCT.md) | Community standards and expectations |
| [Contributing Guidelines](https://github.com/getdeadrecon/deadrecon/blob/main/CONTRIBUTING.md) | How to contribute to DeadRecon |
| [Security Policy](https://github.com/getdeadrecon/deadrecon/blob/main/SECURITY.md) | Reporting vulnerabilities responsibly |
| [License](https://github.com/getdeadrecon/deadrecon/blob/main/LICENSE) | MIT License terms |

---

## 📜 License

MIT License — see [LICENSE](https://github.com/getdeadrecon/deadrecon/blob/main/LICENSE)

Copyright (c) 2026 the-clipper. AI architecture and implementation by Claude (Anthropic).

---

*Built with questionable amounts of caffeine. "Map the surface. Own the signal."*
*Some ghosts leave no trace. This one left commits. — Claude*    
