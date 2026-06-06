# Changelog

All notable changes to PhantomSignal // PHANTOM SIGNAL are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.4.0] — 2026-06-06

### Added
- **16 new intelligence API integrations** — Twitch, Mastodon (4 federated instances), Keybase, Gravatar, HackerNews, Tumblr, Flickr, Spotify, Steam, VK, Telegram (public channels), Discord (user + server), Facebook/Meta Graph, EmailRep, Intelligence X (dark web / paste / breach), and Abstract API phone validation
- **Ghost Key invalid-key indicator** — TEST button in the Ghost Key Vault now detects HTTP 401/403 rejections and surfaces an amber `⚠ INVALID` badge on the key row with a targeted toast message, distinct from generic network failures (`✗ FAIL`)
- **`APIAuthError` exception** (`intel/apis/base.py`) — raised on 401/403 in `_get`; propagates through the orchestrator and is caught specifically by the test endpoint, keeping scan pipelines unaffected
- **WebSocket sync on late join** (`web/app.py`, `terminal.js`) — server emits current scan progress to clients that connect after a scan has already started; eliminates the stuck-at-0% progress bar on page load
- **Polling fallback for live results** (`results.html`) — a background `fetch` loop keeps the progress bar accurate even when SocketIO events are missed (slow connect, missed room join)

### Changed
- **AlienVault OTX timeout fix** — section requests (`general`, `reputation`, `geo`, `malware`, `passive_dns`) now run concurrently via `asyncio.gather` with an 8-second per-section timeout instead of sequentially; eliminates the consistent 30s timeout caused by the slow `reputation` endpoint
- **People aggregator** (`intel/people/aggregator.py`) — now runs free no-key sources as a fallback baseline when no paid people-intel APIs are configured; improved field merging for names, employers, social profiles, and phone numbers; native social API result types (`github_profile`, `twitter_profile`, etc.) mapped directly to social profile slots
- **Config env mappings** (`core/config.py`) — added env var bindings for all 16 new API integrations
- **Socket init timing** (`app.js`) — `initSocket()` called at module load (before `DOMContentLoaded`) so the results page can attach scan room listeners immediately; guarded against double-init
- **Scan start delay** (`core/engine.py`) — 1-second delay before first module fires, preventing WebSocket race where events are emitted before the browser has joined the scan room
- **`.gitignore`** — replaced explicit `.env.local` / `.env.production` entries with `.env.*` wildcard; added `!.env.example` exclusion so a template file can be committed safely; covers `.env.testing` and any future per-environment variants

### Fixed
- Ghost Key TEST showing `✓ OK` with 0 results for an invalid key (e.g. Shodan 403) — now correctly shows `⚠ INVALID`
- AlienVault consistently timing out on IP scans due to sequential section fetches exceeding the 30s orchestrator limit
- Progress bar stuck at 0% when navigating directly to a scan URL mid-run

---

## [1.3.3] — 2026-06-05

### Changed
- **Wordmark logo** — replaced block-character ghost mascot with a `PHANTOM / SIGNAL` slant-font wordmark (neon green glow) across the nav bar, page headings, empty states, and favicon; both words centered on a shared canvas
- **Ghost emoji** — swapped 🦉 → 👻 in UI templates and pre-rendered README SVG screenshots (`screenshot_dashboard.svg`, `screenshot_launch.svg`)
- **CSS sizing** — image sizing switched from height-based to width-based (`120px` nav, `180px` heading, `200px` empty state) to match the new wider image proportions

### Added
- `scripts/render_avatar.py` — source-of-truth script to regenerate the wordmark PNG assets (pyfiglet slant font + Pillow glow layers)
- `docs/assets/phantomsignal-avatar-transparent.png` — transparent variant of the wordmark for light backgrounds

### Removed
- `scripts/render_owl.py` and all owl PNG assets (`owl-ascii.png`, `owl-ascii-transparent.png`)

### Fixed
- Encrypted exporter file magic bytes updated `NOWL` → `NPHM`; legacy `NOWL` files remain readable for backwards compatibility

### Housekeeping
- `wheels/` added to `.gitignore` (offline pip wheel cache — not for version control)
- Dockerfile: optional crawler deps (`chromium`, `tesseract-ocr`) split into a fault-tolerant layer; added offline wheel install via `--find-links`

---

## [1.3.1] — 2026-06-04

### Changed
- **Author rebrand** — all author references updated to `the-clipper` across package metadata, LICENSE, and inline credits.
- **GitHub Sponsors** — added sponsorship links to README, landing page, and `FUNDING.yml`.
- **Assets** — updated org avatar and asciinema recording to reflect PhantomSignal branding.

---

## [1.3.0] — 2026-05-31

### Added
- **Rich CLI scan output** — `phantomsignal scan <target>` now renders module-specific panels instead of a flat table: DNS intelligence (records, subdomains, SPF/DMARC/DNSSEC, cert transparency, zone transfer), port scan table (PORT · SERVICE · PROTO · VERSION · BANNER · RISK), tech stack (detected technologies, security header grade A–F, TLS info), exposed resources (status codes, sensitive path flags), network intel (GeoIP, ASN, TOR/VPN indicators), and a red anomaly callout panel. All panel right-borders are pinned to terminal width.
- **nmap integration in port scanner** — attempts `nmap -sV --version-intensity 7 -O --osscan-guess` for full version detection and OS fingerprinting; falls back silently to the pure-Python async TCP prober when nmap is absent or lacks privileges. Scan engine and OS guess shown in panel footer.
- **Expanded port coverage** — `COMMON_PORTS` grown from 56 → 99 ports covering low privileged and high-numbered services (WinRM, Webmin, InfluxDB, Radmin, and more). `DANGEROUS_PORTS` extended with WinRM, REXEC, RLOGIN, FINGER, RPCBIND, Radmin, and Webmin.
- **Web results type-aware rendering** — results page renders each result type as structured output matching CLI panels instead of raw JSON blobs. Covers open ports, OS detection, DNS records, email security, security posture grade, TLS, API endpoints, IP geolocation, and more.

### Changed
- **Quick probe** now runs all 5 CLI-default modules (`dns_recon`, `port_scan`, `tech_detect`, `api_hunt`, `intel`) — previously ran only 3.
- **Full mission form** — `web_crawl` unchecked by default to match CLI behaviour.
- **API route** empty-modules fallback uses the same 5-module default as CLI.
- **`.gitignore`** — `scans/` → `/scans/` to avoid shadowing `phantomsignal/web/templates/scans/`.

---

## [1.2.5] — 2026-05-30

### Fixed
- README demo images not rendering on PyPI — replaced relative `docs/assets/` paths with absolute `raw.githubusercontent.com` URLs

---

## [1.2.4] — 2026-05-30

### Changed
- Added `Homepage` and `Documentation` URLs pointing to phantomsignal.sh in PyPI project metadata

---

## [1.2.3] — 2026-05-30

### Fixed
- Web UI navbar brand link displayed "NIGHTOWL" instead of "PHANTOMSIGNAL"

---

## [1.2.2] — 2026-05-30

### Fixed
- `phantomsignal web` crash on all platforms — missing `allow_unsafe_werkzeug=True` in `socketio.run()` call in CLI entrypoint
- Windows asyncio compatibility — force `WindowsSelectorEventLoopPolicy` on Python 3.10+ to prevent `aiodns` conflict with `ProactorEventLoop`

---

## [1.2.1] — 2026-05-30

### Fixed
- PyPI project description updated with correct asciinema recording URL and PyPI badge

---

## [1.2.0] — 2026-05-30

### Changed
- **Project renamed from NightOwl to PhantomSignal** — all references updated across codebase, docs, config, and assets
- Domain migrated from `owlrecon.io` → `phantomsignal.sh`; DNS configured with GitHub Pages A records
- GitHub org renamed `nightowl-osint` → `phantomsignal`; repo renamed `nightowl` → `phantomsignal`
- Python package renamed `nightowl` → `phantomsignal`; CLI entry point `nightowl` → `phantomsignal` (`owl` alias preserved)
- Config directory `~/.nightowl/` → `~/.phantomsignal/`; config file `nightowl.yaml` → `phantomsignal.yaml`
- Database default `nightowl.db` → `phantomsignal.db`
- Environment variable prefix `NIGHTOWL_*` → `PHANTOMSIGNAL_*`
- ASCII banner art regenerated for PHANTOMSIGNAL in `__init__.py`, README, and all demo assets
- Owl PNG graphic updated — footer label changed from "NightOwl" to "PhantomSignal" in both dark and transparent variants
- Demo GIF and asciinema cast regenerated with PHANTOMSIGNAL banner and `phantomsignal` CLI command
- SVG screenshots regenerated with updated PHANTOMSIGNAL branding throughout
- GitHub Pages landing site fully rebranded — nav, hero title, footer, and og tags
- GitHub org profile README rebranded with new ASCII art, updated badges and links
- GitHub repo About description and homepage URL updated to `phantomsignal.sh`
- Contact email updated to `security@phantomsignal.sh` across all docs

### Added
- Code of Conduct (`CODE_OF_CONDUCT.md`) — operational security standards for contributors and community members
- Security Policy (`SECURITY.md`) — coordinated disclosure process, scope definition, and timeline commitments
- Pull Request template (`.github/PULL_REQUEST_TEMPLATE.md`) — structured template with security considerations and authorization affirmation sections
- `CHANGELOG.md` — full project history from 1.0.0, following Keep a Changelog format with semver comparison links
- Phantom Dawn light theme screenshots for all three web UI views on the GitHub Pages landing site
- GitHub Pages site badge in README
- Changelog badge in README
- Topics section to README with 20 linked topic badges, each linking to the corresponding GitHub topic search page
- `// SIGNAL CATEGORIES` topics section on the GitHub Pages landing site

### Fixed
- "Install Now" CTA was incorrectly pointing to the GitHub repo instead of the on-page quickstart section

---

## [1.1.0] — 2026-05-28

### Added
- GitHub Pages project landing site at `https://phantomsignal.sh` (`docs/`)
  - Hero section with install block and copy button
  - Features grid, capabilities breakdown, quickstart tabs, and intelligence grid
  - Asciinema demo embed and SVG web UI screenshots
  - CTA section and project footer
- Phantom Dawn light mode theme — soft blue-grey palette, muted accent colours, matrix rain disabled, ASCII owl logo variant; toggleable via the `☀/🌙` button in the navigation bar; preference persists across sessions via `localStorage`
- Owl ASCII art render script for generating the light-theme logo asset
- User documentation (`docs/USAGE.md`) — comprehensive guide covering installation, CLI usage, web UI, ghost run profiles, module reference, export formats, and API key setup

### Changed
- Web UI navigation updated to link DOCS to `docs/USAGE.md` on GitHub
- README demo section updated with light/dark theme toggle documentation

### Fixed
- All DOCS links across the web interface and landing site now point to `docs/USAGE.md` on GitHub

---

## [1.0.0] — 2026-05-25

### Added
- Initial release of PhantomSignal — open-source OSINT intelligence framework
- CLI interface (`phantomsignal`) with ghost run profiles: Quick Probe, Standard Recon, Deep Dive, Ghost Mode
- Web interface (Flask + SocketIO) with Shadow Grid dashboard, live feed, scan launch, and results views
- Plugin/module API system with `@register_api` decorator for auto-registration
- Intelligence modules: DNS Recon, Port Scanner, Tech Detector, Web Crawler, API Hunter, People Intel, Intel APIs (Shodan, VirusTotal, AbuseIPDB, HaveIBeenPwned, Censys)
- Export pipeline: JSON, CSV, HTML, PDF, XLSX, STIX 2.1, XML, Markdown; all formats support ZIP compression and AES-256-GCM encryption
- Shadow Score — aggregate risk scoring system per scan
- GitHub Actions CI workflow (lint, test, build checks on push and PR)
- `CONTRIBUTING.md` with dev setup, plugin authoring guide, and PR guidelines
- CI status badge in README
- README demo section: animated CLI demo (GIF + asciinema cast), SVG web UI screenshots

### Fixed
- Repository URLs corrected to `phantomsignal/phantomsignal` across all files and badge links

---

[Unreleased]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/getphantomsignal/phantomsignal/releases/tag/v1.0.0
