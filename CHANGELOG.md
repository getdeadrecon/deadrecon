# Changelog

All notable changes to PhantomSignal // PHANTOM SIGNAL are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.29.2] - 2026-11-03

### Fixed
- **Port scans from the web console work.** The form sent a profile name where the scanner
  expected a list of ports, so every console scan using `port_scan` reported no open ports. The
  profile now takes effect, and `port_scan_fast` handles it too. These scans now send
  real probes from your IP, and the report marks them as attributable.
- **`--modules` rejects unknown names.** They were skipped silently, so the documented
  `--modules dns,port,tech` ran nothing and still reported a completed scan. Comma-separated
  names now work, as does repeating the flag.
- **`--format xlsx` works on the CLI.** The README and console offered it, but the CLI refused it.
- **`phantomsignal init` points at Integrations** for API keys, instead of a page that doesn't exist.
- **The console's scan profile cards say what the profiles do.** They promised modules, port
  ranges and durations that profiles don't control. The common port option said 67 ports, not 99.

### Documentation
- **The usage guide lists every command and scan flag.** It had wrong defaults, a missing
  scan type, and claimed the scan type was auto-detected.
- **Scan profiles are described as they work.** Deep runs the same modules and ports as Standard.
- **Corrected the database path, log location and Docker volume name** in troubleshooting.

## [1.29.1] - 2026-11-03

### Changed
- **Tor scans explain a Partial grade.** The scan report and CLI now say when every counted
  request went through Tor and the grade is Partial only because of TLS fingerprinting. The
  CLI also confirms the scan was on Tor. The grade itself is unchanged.

### Fixed
- **The CLI's API key hint works.** It pointed at `phantomsignal config --list-apis`, which doesn't
  exist; it now points at `phantomsignal status`, as does the site.

### Documentation
- **The PyPI page, README and project site now cover 1.29.** The PyPI page had still led with
  1.27.0, and its relative links were broken.
- **Corrected claims that went too far.** Not every network source uses the stealth layer: keyed
  API providers and some keyless sources connect directly unless Tor is on. The source count is
  now 50+ rather than 54+, and "Provably Masked" is gone from the site.
- **Quick starts mention the first-run setup token**, and the README no longer points at a config
  file that isn't in the repo.
- **`docs/RELEASING.md` matches the current API-token setup**, and sets the token through a
  hidden prompt.

## [1.29.0] - 2026-11-02

### Security
- **DNS no longer leaks past the proxy.** With a proxy configured, DNS lookups use
  DNS-over-HTTPS through the proxy and never fall back to the system resolver. SOCKS
  proxies now resolve hostnames remotely under TLS impersonation too.
- **The OPSEC grade now reflects real traffic.** All outbound HTTP is counted, a module
  that sends a direct request is reported as attributable, and nothing can read as
  masked or quiet without a proxy. It was verified against packet captures of every module.
- **"Masked" is harder to earn.** Nearly every request must be proxied and impersonated,
  from stealth-level modules only. The report also names tools that use local DNS.
- **`subfinder` no longer bypasses the proxy.** It connected directly to crt.sh's database,
  so it now skips that source when proxied, which reduces coverage.
- **`nuclei` is now reported as attributable, even with a proxy.** With a proxy set, its full
  template set still connects directly to the target and to third parties such as
  `checkip.amazonaws.com`, and sends names to your local DNS resolver. Proxied runs now use
  HTTP templates and an unreachable resolver list, which removes most of this traffic but
  not all of it. Don't rely on a proxy to hide `nuclei` scans.
- **Six more modules now honor proxies:** `dns_recon`, `subdomain_enum`, `archive_mine`,
  `username_enum`, `profile_pivot` and `email_oracle`, along with `takeover` and `darkweb`.
  Public suffix data is no longer downloaded at runtime.
- **Fewer direct connections while proxied.** Zone transfers, direct nameserver queries,
  raw TLS and JARM probes are skipped when a proxy is configured, so those results
  won't appear. Shodan and Wayback lookups in stealth-tagged modules now use the proxy.
- **The web crawler now honors proxies.** It was rebuilt on the stealth client, so it
  also gets adaptive pacing, attribution reporting and the network guard.
- **DNS rebinding is blocked** for direct HTTP, including TLS impersonation, by re-checking
  each connection and pinning it to the vetted address.
- **Pivots can't be steered to internal addresses.** A public target can no longer pivot
  to private or metadata IPs. Set `PHANTOMSIGNAL_ALLOW_METADATA=true` to test a metadata
  service deliberately.
- **Scan targets are validated** in the web console, REST API and CLI.
- **Content-Security-Policy added.** It limits where the console can load from and send
  data to. Inline scripts need a per-response nonce and inline handlers are blocked, so
  markup injected from scan data can't run script. Inline styles are still allowed.
- **Tor now works, in one click.** The old setting saved and showed "Tor" in the navbar
  while scans connected directly, and the Docker Tor container was never connected to the
  app. Now the 🧅 button starts Tor for you: it uses a Tor already running, or the installed
  program, or downloads the official bundle checked against a pinned hash. Tor is also built
  into the Docker image, which replaces the old container from 2021.
- **Tor fails closed.** Each scan confirms it's on Tor before touching the target and stops
  if it can't. All HTTP and DNS use Tor, including keyed APIs and alert webhooks, and targets
  get separate circuits. Modules that would bypass Tor are skipped and listed in the report.
  TLS impersonation and `quiet` pacing turn on automatically.
- **XML from scanned targets is parsed safely.** Document metadata and nmap output now use
  `defusedxml`, so a crafted document can't use entity expansion against the scanner.
- **`.onion` addresses can't leak.** They're refused without Tor instead of being sent to a
  DNS resolver, and only modules that contact nothing but the target run against them.
- **The Covert profile now does something.** It was stored but ignored. It now uses
  `paranoid` pacing and skips modules that connect directly from your IP.
- **One browser identity per target across a scan.** Each module used to pick its own, so
  a target could see several browsers from one IP.
- **Reports no longer imply a clean result when non-HTTP traffic went direct.** A scan with
  a port scan could read "100% proxied, 0 direct". The report now names those modules.
- **No map tiles by default.** A tile provider sees which areas you view, and the default
  provider had started refusing requests. Maps plot points with no background until you
  set `geo.tile_url`.
- **External tools that can't use a proxy now count as direct.** They were counted as
  proxied when a proxy was configured, which inflated the proxied percentage.
- **Timed-out external tools are killed.** They kept running, and kept scanning, after
  being reported as timed out.
- **The Docker image runs as a non-root user under gunicorn**, with dependencies pinned
  by hash in `requirements.lock`. `nmap` keeps only the raw-socket capability.
- **Scanned sites can't steer requests inward.** Direct HTTP requests never contact
  cloud metadata or link-local addresses, and a public site can't redirect to a
  private address. Operators can still scan private targets directly.
- **Links and map popups are safe from scan data.** Links only accept `http(s)` URLs,
  and Geo Recon and Locate popups escape their fields. A case name can no longer
  break out of its delete confirmation.
- **CDN scripts are integrity-checked**, so a tampered socket.io or Leaflet file won't
  load in the signed-in console.
- **CI hardening:** workflows pin actions to commit SHAs, and CI runs with read-only
  repository access. Requests over 16 MB are refused.

### Fixed
- **Pages compressed with Brotli can be read without TLS impersonation.** The stealth
  client advertised Brotli without a decoder installed, so modules received unreadable
  bytes from those servers and could miss findings. This also broke the Identity page's
  TLS lookup in Docker.
- **Origin Pivot findings display again.** They were stored without their type, so the
  CDN and origin results never appeared in the scan view.
- **`tls_fingerprint` works.** It passed flags tlsx rejects, so it never ran.
- **Failed external tools now report it.** They show an `external_tool_error` finding,
  instead of looking like a clean scan with no results.
- **The web crawler works again.** It crashed on a missing module, so crawls produced
  nothing. It no longer needs Scrapy or Twisted.
- **Sign-in pages no longer throw a script error**, and Sign out stays on screen at
  every width.

### Added
- **Optional Go tools in Docker.** Build with `--build-arg RECON_TOOLS=true`, or set
  `PHANTOMSIGNAL_RECON_TOOLS=true` for Compose, to include nuclei, katana, subfinder, naabu
  and tlsx. Downloads are pinned by SHA-256, and the image grows by about 500 MB.
- **`--tor` and `phantomsignal tor on|off|status` on the CLI**, and `PHANTOMSIGNAL_TOR_HOST`
  and `PHANTOMSIGNAL_TOR_PORT` for pointing at your own Tor service.
- **The Identity page confirms Tor** with `check.torproject.org` and shows your exit.
- **The attribution report says when counts include external tools.** Each run counts as
  one request because a tool's own requests can't be seen, so the real total is higher.

### Changed
- **`curl_cffi` 0.17 or newer is required**, and `brotli` is a new dependency.
- **Docker upgrades need a one-time step.** The container no longer runs as root, so
  volumes made by 1.28.0 or earlier must be handed over to it:
  `docker compose run --rm --user root phantomsignal chown -R app:app /app/data /app/exports /home/app/.phantomsignal`.
  The saved-settings volume also moved to `/home/app/.phantomsignal`.
- **`PHANTOMSIGNAL_HOST` and `PHANTOMSIGNAL_PORT` no longer apply in Docker.** Change
  the published port in `docker-compose.yml` instead.

---

## [1.28.0] — 2026-11-02

**Console login and data protection.** The web console now requires sign-in,
stored data is private to your user, and packages and the Docker image install
correctly. This release has breaking changes; see **Changed**.

### Security
- **The web console now requires a login.** A single operator account protects
  every route, created on first run with a setup token printed to the server log.
  New CLI commands: `phantomsignal set-password` and `phantomsignal api-token`.
- **CSRF protection** on every browser form and session-authenticated API write.
- **Socket.IO** now refuses anonymous connections and other origins. Allow a
  reverse proxy's URL with `PHANTOMSIGNAL_ALLOWED_ORIGINS`.
- **`~/.phantomsignal/config.yaml` is written owner-only** (`0600`, directory
  `0700`). It held API keys and was world-readable.
- **The SQLite database is now owner-only** (`0600`, including `-wal`/`-shm`).
  Existing files are tightened on next start.
- **Local builds can no longer package private data:** wheels and sdists exclude
  `tests/` and `config/`, and `.dockerignore` keeps databases, keys, `.env.*`,
  `config/`, `tests/` and exports out of images. `.gitignore` also covers more key
  and database formats, plus Locate exports.
- **Docker Compose publishes on loopback only**, including the optional Tor ports.
- The session signing key now persists in `~/.phantomsignal/secret_key`, so logins
  survive a restart. Password login failures are throttled per client.

- **TLS is now verified for API sources that can carry credentials**, including
  Shodan calls in `origin_pivot`. They previously accepted any certificate, so a
  hostile proxy could have captured GitHub, OpenFEC, OpenCorporates or Shodan keys.
- **HTML and PDF reports escape scan data**, so a scanned site can't inject script
  into a report.
- **Exports no longer default to `/tmp`.** They go to `~/.phantomsignal/exports`
  (`0700`) as owner-only files that refuse to overwrite existing paths or symlinks.
  Files downloaded through the web console are deleted from disk afterward.
- **The Identity page and live feed escape external data**, closing a script
  injection path through plain-HTTP egress lookups.

### Fixed
- **Signature templates now ship in wheels and sdists.** Installs from PyPI loaded
  0 of the 4 templates, with no error.
- **The Docker image builds from a fresh clone.** It no longer needs a pre-downloaded
  `wheels/` folder, and it drops the unused Playwright, Chromium and Tesseract layers.
- **Docker keeps saved settings across upgrades.** API keys, console settings and the
  session key now live on a volume, instead of being lost when a container is recreated.
- CI and the publish workflow now check package contents. CI also installs the wheel
  in a clean environment, and builds and boots the Docker image.

### Changed
- **Smaller install:** 36 declared packages that the code never imports directly were removed.
- **Dev tools moved** to `requirements-dev.txt`; install them with `pip install -e ".[dev]"`.
- **Exports:** the default directory moved; set `PHANTOMSIGNAL_EXPORT_DIR` to override.
- **Breaking:** REST API calls need `Authorization: Bearer <token>`.
- **Breaking:** `GET /api/v1/health` returns only `status` unless signed in.
- **Breaking:** the Compose port binding no longer accepts remote connections.
  See "Signing in" in `docs/USAGE.md` for reverse-proxy setup.

---

## [1.27.0] — 2026-07-19

**Identity-intelligence expansion + egress UX.** The Profiler gains eight
keyless public sources and finally persists its runs as scans; free proxy pools
are one click away; and the whole stealth posture is now visible and durable.

### Added
- **Eight keyless identity sources** (`intel/apis/identity_sources.py`) — no API
  key required, feeding the Profiler aggregator's existing fields:
  - **XposedOrNot** — breach exposure by email, filling the keyless-breach gap
    (HIBP/IntelX need keys).
  - **GitHub commit-email harvester** — real name + email mined from a user's
    public commits and events.
  - **GitLab** — public profile, links, and public email.
  - **Wikidata** — structured biographical identity for named people (DOB,
    official site, cross-linked socials); human-only (rejects same-name
    companies/films).
  - **WebFinger** — resolves a fediverse handle to its profile and aliases.
  - **Offline phone intel** (libphonenumber) — region, carrier, line-type, and
    validity with **zero network egress**.
  - **openFEC** — US political-donation records → employer / occupation / city.
  - **OpenCorporates** — company-officer roles for a name.
- **Profiler runs are now scans.** A Profiler search persists as a `people_intel`
  scan — `Scan` + `ScanResult` rows + a linked `ShadowProfile` — so it appears
  under **Scans** with history, summary, and export. Added a **"View in Scans"**
  button, a `people_intel` path in the CLI `profile` command, and a new
  **People & Identity** category in the scan summary view.
- **Keyless sources routed through the stealth client** — a `STEALTH_ROUTED`
  opt-in on `BaseIntelAPI` routes those sources through the shared proxy pool +
  adaptive rate limiter, and records them in the attribution ledger (proxied when
  a proxy is configured, instead of leaking direct and uncounted). Keyed
  providers are untouched. The offline phone source makes no request.
- **Egress-posture chip in the navbar** — a **STEALTH / PARTIAL / DIRECT** badge
  beside the connection status, theme-aware, tooltip'd with profile · pool size ·
  rotation · JA3 · Tor, linking to Scan Settings. Backed by
  `core.http.stealth_status()`.
- **Proxy-pool seeding** (`core/proxy_sources.py`, Settings → Scan Settings) —
  fetch from curated free feeds (ProxyScrape, TheSpeedX, monosans, Proxifly), a
  custom list URL, or **upload a list file**. Tolerant parser handles
  `ip:port`, `scheme://ip:port`, `user:pass@ip:port`, and `ip:port:user:pass`,
  with de-dupe and per-import (300) / total (1000) caps.
- **Settings persistence** — scraper/egress settings (stealth profile, single
  proxy, pool, rotation, TLS impersonation, Tor, robots.txt, delay, concurrency)
  now survive a restart via `~/.phantomsignal/config.yaml`, merged non-
  destructively. `config.persist()` deliberately does **not** copy env-provided
  API keys into the file.

### Fixed
- **Profiler results page crashed** (KeyError) whenever a social profile was
  found — the template iterated the `social_profiles` dict as if it were a list.
- **Dark-mode dropdowns** — native `<option>` menus fell back to the OS light
  theme; now themed for every select, and the stealth/pool/retention/kind/mode
  selects gained the styled dropdown arrow.

### Dependencies
- Added `phonenumbers` (offline phone metadata; degrades gracefully if absent).

---

## [1.26.0] — 2026-07-15

**Best-of-breed engines + the vuln loop.** PhantomSignal now closes the ASM loop
(maps the surface *and* flags what's exploitable) and orchestrates fast Go-native
recon tools when installed — all under stealth governance, with pure-Python
fallback so a binary-free install keeps working.

### Added
- **Vulnerability scanning via nuclei** (`scrapers/vuln_scanner.py`, module
  `vuln_scan`) — emits the `vulnerability` result type (long-weighted in the
  shadow score, never produced until now) with normalised severity; a
  `vuln_scan_summary` rolls up counts. Surfaces in the Findings & Exposure
  category with severity grading, and exports as a **STIX 2.1 Vulnerability SDO**.
- **External-tool adapter framework** (`scrapers/_external.py`) — availability-
  gated on `shutil.which`, proxy injected from the shared egress config, output
  tagged `proxied` (or honestly `attributable` when the tool can't proxy);
  `run_with_fallback()` runs the native module when a binary is absent or empty.
- **Speed adapters** (all opt-in, native fallback where one exists):
  - `subdomain_enum_fast` — **subfinder** (proxied) → native enumerator.
  - `port_scan_fast` — **naabu** (attributable, raw-socket) → native scanner.
  - `web_crawl_fast` — **katana** (proxied when a proxy is set) → native crawler.
  - `tls_fingerprint` — **tlsx** (attributable) JARM + cert hashes; complements
    infra_pivot (no standalone fallback).
- **Honest dynamic OPSEC** (`effective_opsec`) — a module's attribution grade
  reflects its *actual* egress posture, not just the static registry tag.

### Changed
- Scraper registry gains a `default` flag; loud/active or alternative modules
  (`vuln_scan`, `*_fast`, `tls_fingerprint`) stay out of the full-spectrum sweep
  and are opt-in. New modules exposed in the CLI `--modules` list and web form.

---

## [1.25.0] — 2026-07-15

**OPSEC Core** — makes the stealth layer the visible flagship. PhantomSignal now
reports its own **attribution surface**: after every scan, an honest answer to
*"what did this scan leak about my infrastructure?"*

### Added
- **Attribution Surface report** — a per-scan OPSEC panel on the summary page
  grading the run (`masked` / `partial` / `exposed` / `quiet`) from real
  telemetry: % of requests proxied vs. sent direct from your IP, which JA3/JA4
  browser profiles were presented, WAF challenges hit, and adaptive backoffs.
  Emitted as an `attribution_surface` finding (excluded from the Risk Score) and
  broadcast live over the scan socket.
- **`AttributionLedger` + `attribution_scope()`** (`core/http.py`) — a
  contextvar-scoped ledger that every `StealthClient` request records into,
  wherever it runs in the module tree. No per-scraper wiring required.
- **`OpsecLevel` taxonomy** (`intel/opsec.py`) — every module declares how
  attributable its traffic is (`stealth_guaranteed` / `proxied` /
  `attributable`), stamped onto each finding. Grading is deliberately honest —
  any attributable module or under-50%-proxied traffic caps the grade.
- **Scraper module registry** (`scrapers/registry.py`) — a `@register_module`
  plugin registry mirroring the intel-API pattern; replaces the engine's
  hard-coded module table so new modules join the pipeline by registering.
- **`StealthClient.stream()`** — stealth-routed streaming downloads (proxy pool +
  browser identity + adaptive pacing) with mid-flight size-capping.

### Changed
- **Document-metadata downloads** now route through the stealth client instead of
  a `PhantomSignal-OSINT/1.0` scanner User-Agent hitting the target directly.
- **Engine pipeline** is resolved from the scraper registry; each built-in is
  tagged with its verified OPSEC level (7 route through the stealth client;
  Tor-based dark-web egress is proxied; raw-socket and third-party-API modules
  are honestly marked attributable).

---

## [1.24.0] — 2026-07-12

Simplified the web console to two themes and removed the pre-rendered demo /
screenshot assets in favour of richer written descriptions.

### Changed
- **Themes cut to two**: the opt-in **Neon** theme was removed; the console now
  ships **Dark** (default) and **Light** only. The `:root[data-theme="neon"]`
  token block, the third nav toggle, and the now-dead `cycleTheme()` helper were
  deleted. Legacy `--neon-*` colour-utility aliases are unaffected — they resolve
  to the active theme's role tokens.
- **README banner**: replaced the ASCII-art logo block with the project name and
  tagline.
- **README + landing page**: the "Demo" / "Live Demo" sections no longer embed a
  screenshot GIF or asciinema recording. They now show a plain-text terminal
  transcript plus a written breakdown of each scan stage, and the functional
  copy was expanded throughout.
- **De-cyberpunk pass**: removed "cyberpunk" / "Phantom Dawn" flavour wording from
  the README, `USAGE.md`, `web/app.py`, and the About page, and dropped the
  landing page's animated matrix-rain canvas and CRT scanline overlay (elements,
  CSS, and JS).
- **"Ghost Mode" → Covert / Evasive**: brought the public docs in line with the
  app's plain-language terminology. The README feature, landing-page callout, and
  `USAGE.md` now describe the **Covert** scan profile and **Evasive (low & slow)**
  toggle instead of "Ghost Mode"; corrected the CLI reference (`--profile covert`,
  not `ghost`; dropped the non-existent `--ghost` flag). The Docker Tor sidecar
  compose profile was renamed `ghost` → `covert` (`docker-compose --profile covert`).
- **USAGE.md nav-terminology sync**: brought the full user guide in line with the
  app's current plain-language UI — "Ghost Run(s)" → **Scans**, "New Mission" →
  **New Scan**, "Ghost Keys" → **Integrations**, "Quick Probe" → **Quick Scan** /
  the **Quick** profile, "Shadow Grid" → **Dashboard**, "Shadow Profiler" →
  **Profiler**, "Shadow Score" → **Risk Score**, profile names Standard/Deep, and
  the "Start Scan" button — including the nav map, section headings, and TOC anchors.
- **GitHub Pages retheme**: the landing site (`docs/index.html`, `docs/site.css`)
  was recoloured from the coral/neon marketing palette to the app's default Dark
  theme — deep-slate surfaces, federal-blue hero, steel-blue links, gold accents,
  restrained glow, and an app-aligned green → amber → red risk-score ramp. README
  and landing-page shield badges were updated to the same blue / steel / gold.

### Removed
- `docs/assets/demo.gif`, `docs/assets/demo.cast`, `docs/assets/screenshot_cli.svg`,
  and the `scripts/gen_assets.py` generator (its only outputs were the removed
  demo / screenshot assets).
- The asciinema embed and "play it locally" instructions from the README.
- The figlet ASCII-art blocks from the landing page — the hero banner and the
  "Ready to run a scan?" CTA banner — leaving the styled `PHANTOMSIGNAL` wordmark
  and headings (hero recentred to a single column).
- **All sponsorship / funding solicitation**: the GitHub Sponsors badge and
  "Sponsors" tier section in the README, the landing page's nav / footer sponsor
  links and sponsor-tier section (plus its CSS), and `.github/FUNDING.yml`.

---

## [1.21.0] — 2026-07-11

Operations-console theme system — a ground-up redesign of the web UI's theming
onto a USWDS-style semantic token model, with a full accessibility pass to W3C /
WCAG 2.1 AA. Moves the default look off neon-green-on-black to a restrained slate
console with an indigo→cyan accent, while preserving the original neon look as an
opt-in "cyberpunk" theme.

### Added
- **Role-token design system** (`web/static/css/phantomsignal.css`): semantic
  tokens (`--surface-*`, `--ink-*`, `--accent*`, `--success`/`--warning`/
  `--danger`/`--info`) are the single source of truth; components consume roles,
  never raw hues. Tints use `rgba(var(--<role>-rgb), a)` so one component rule
  recolours across every theme. Legacy `--neon-*` / `--dark-bg` / `--text-*` names
  are retained as aliases so existing markup keeps working.
- **Three themes + System**: **dark** (operations console, default), **light**,
  and **cyberpunk** (the legacy neon look, intact). A nav control cycles
  System → Light → Dark → Cyberpunk; **System** carries no `data-theme` and
  follows `prefers-color-scheme` live.
- **Severity semantics**: colour is reserved for status — green = success, amber =
  warning, red = danger, cyan/indigo = interactive — instead of decoration.

### Accessibility (W3C / WCAG 2.1–2.2)
- Every text and UI token verified to meet **AA contrast** (≥4.5:1 text, ≥3:1
  form-control borders); fixes the previously-failing muted-text and border tokens.
- `color-scheme` property + `<meta name="color-scheme">` so native controls,
  scrollbars, and form fields render in the active scheme.
- A single high-contrast **`:focus-visible`** keyboard indicator across
  interactive elements (2.4.7 / 2.4.13).
- **`prefers-reduced-motion`** block that disables the matrix rain, scanlines,
  glitch layers, and cuts transitions (2.2.2 / 2.3.3).
- Retro effects (matrix rain, scanlines, glitch) are now confined to the
  cyberpunk theme; the matrix canvas also respects reduced-motion in JS.

### Notes
- No Python surface changed; 147 tests pass. Verified visually via Playwright
  across dark / light / cyberpunk on the dashboard, scan form, and settings pages.

## [1.20.0] — 2026-07-11

Auto-diff on scan completion + new-asset alerting — the second Phase 5 (ASM
monitoring) module. Change detection now runs automatically at the end of every
ghost run, and new sensitive assets are pushed to a notification webhook instead
of waiting to be noticed in a report.

### Added
- **Auto-diff on scan completion** (`core/engine.py`): when a ghost run finalizes
  (status → `COMPLETE`), the engine diffs it against the previous completed scan
  of the same target, stores the resulting `asm_change` / `asm_diff_summary`
  findings against the new scan, and emits an `asm_diff_complete` summary to the
  live grid. The very first scan of a target has no baseline and is skipped.
  Best-effort: an auto-diff failure never fails the scan.
- **New-asset alerting** (`intel/asm_alert.py`): when new **sensitive** assets
  appear (a fresh subdomain, open port, credential exposure, leak, …), the engine
  emits an `asm_alert` event and delivers a webhook payload to
  `notifications.webhook_url`. The payload carries both `text` (Slack
  incoming-webhook shape) and `content` (Discord shape) plus a structured
  `assets` list, so one generic POST works against Slack, Discord, or a custom
  endpoint. No webhook configured → the event/log still fire, delivery is skipped.

### Correctness & validation
- The alert payload builder is pure and unit-tested (summary extraction,
  new-sensitive filtering that excludes removed/non-sensitive assets, Slack +
  Discord payload shapes, long-list truncation). 7 new tests
  (`tests/test_asm_alert.py`); 147 tests pass.
- End-to-end verified against a temp DB with an in-process webhook receiver:
  two scans of a target → 2 new sensitive assets detected, findings stored,
  `asm_diff_complete` + `asm_alert` emitted, webhook delivered with the correct
  payload.

Next in Phase 5: Playwright visual recon / screenshots of discovered web assets.

---

## [1.19.0] — 2026-07-10

Attack-surface diff engine — the first Phase 5 (ASM monitoring) module. Turns
single-shot recon into change detection over time.

### Added
- **ASM diff** (`intel/asm_diff.py`): compares two scans of the same target and
  surfaces what changed — **new** assets (a fresh subdomain, open port, leak, or
  credential exposure), **removed** assets, and **modified** ones (a service
  version/banner that moved). New sensitive assets are flagged as alerts.
  - Pure, unit-tested diff engine (operates on two result-dict lists, no DB):
    `result_key` gives each asset a stable identity (via `IDENTITY_FIELDS` with a
    canonical-hash fallback; summary/meta results are skipped); `state_signature`
    / `changed_fields` detect modifications while ignoring volatile fields
    (timestamps, discovered dates, scan engine); `diff_results` →
    `AsmDiff(added, removed, modified)`; `build_diff_findings` emits `asm_change`
    (new sensitive assets → anomalies) and `asm_diff_summary`.
  - `ASMDiffer.diff_target` loads the two most recent completed scans of a target
    from the DB and diffs them.
  - CLI `psig diff <target>` command with a change panel.

### Correctness & validation
- The diff engine is pure and fully unit-tested (keying, volatile-field
  handling, added/removed/modified detection, sensitive-asset alerting).
  7 new tests (`tests/test_asm_diff.py`); 140 tests pass.

Next in Phase 5: auto-diff on scan completion + alerting, and Playwright visual
recon / screenshots.

---

## [1.18.0] — 2026-07-10

Email-account discovery — the final Phase 4 (identity) module, completing the
identity + dark-web arc.

### Added
- **Email oracle** (`scrapers/email_oracle.py`, `email_oracle` module): given an
  email, discovers which services it is registered on, keylessly, via account-
  existence oracles.
  - **Anchor oracle: Gravatar** — a reliable keyless check (avatar 200 vs 404)
    whose public profile JSON also yields display name, employer, job title,
    location, and **linked social accounts** (twitter/linkedin/github/…),
    feeding the identity graph (`username_enum` / `profile_pivot`).
  - Pure, unit-tested core: `is_valid_email`, `email_md5`,
    `classify_oracle_response` (data-driven `exists`/`not_exists`/`unknown`),
    `parse_gravatar_profile`. `GET_ORACLES` is a data-driven rule schema so more
    existence oracles can be added without code changes.
  - Skips non-email targets. Emits `email_account`, `email_profile`,
    `email_linked_account` (per linked social), and `email_oracle_summary`.
    Wired into the engine (`-m email_oracle`), a CLI panel, and the web form.

### Honest scope
- Password-reset/registration oracles for large sites are fragile and
  ToS-sensitive; hand-authored rules would be silently wrong. The shipped oracle
  set is the ones we can verify (Gravatar), and the classifier is extensible.
  Verified live against Gravatar. 6 new tests; 133 tests pass.

---

## [1.17.0] — 2026-07-10

Dark-web category, part 2 — stealer-log credential correlation and Tor `.onion`
enrichment. Extends the `darkweb` module.

### Added
- **Stealer-log / combolist correlation** (the modern breach signal):
  `parse_combolist` ingests caller-supplied dump files
  (`darkweb.combolist_paths`) and correlates them to the authorized target —
  `email:password` (also `;`/`|`) and stealer **ULP** (`URL:login:password`)
  lines. Emits `corporate_credential` (a `…@target` address) and
  `service_credential` (a login **for** the target's service).
  - **Guardrails:** results are target-scoped, and **every password is masked**
    (`redacted(N)`, length only) before it leaves the parser — plaintext secrets
    are never stored or emitted. This stays a breach-*exposure* monitor.
- **Tor `.onion` enrichment** (opt-in, `darkweb.tor_enrich`): reaches ransomware
  claim onion URLs over a SOCKS proxy. `tor_available()` checks both `socksio`
  and a live daemon and **degrades to a `tor_unavailable` note** when either is
  missing (no hard failure). `socksio` added to requirements for the opt-in path.
- CLI dark-web panel now shows masked credential exposures and Tor status.

### Deferred (honestly)
- **Ahmia** onion search (results are JavaScript-only — no server-side HTML to
  parse) and **paste sweeps** (psbdmp/scylla were DNS-unreachable to verify) are
  not shipped rather than guess at parsers that would be silently wrong.

### Correctness & validation
- `parse_combolist` (scoping, ULP + delimited formats, masking) and the Tor
  degradation path are pure/unit-tested; `run()`'s masked `credential_exposure`
  emission is covered end-to-end. 6 new tests; 127 tests pass.

---

## [1.16.0] — 2026-07-10

Dark-web leak-exposure monitoring — the third Phase 4 module (part 1 of the
dark-web category). Defensive breach-exposure tracking for an authorized target.

### Added
- **Dark-web monitor** (`scrapers/darkweb.py`, `darkweb` module): checks whether
  the authorized target appears on a **ransomware leak site**, via the keyless,
  clearnet ransomware.live v2 API (parsed against the verified record schema).
  Emits `ransomware_exposure` (group, dates, claim URL, infostealer-data flag)
  and `darkweb_summary`. Wired into the engine (`-m darkweb`), a CLI panel, and
  the web scan form.

### Guardrails (built in; enforced for the part-2 stealer-log work)
- **Target-scoped** — `victim_matches_target` confirms a fuzzy leak-site hit
  actually concerns this domain before reporting. A **domain match** is a strong,
  anomaly-raising alert (confidence 0.95); a **name match** is advisory only
  (0.6, not an anomaly), since fuzzy search on a common brand is noisy. Junk
  victim strings (scraped-HTML fragments) are rejected from name-matching.
- **No credential store** — `mask_secret()` redacts any credential-shaped value
  to `[redacted:N]` (length only, never plaintext), keeping this a breach-
  *exposure* monitor rather than a credential harvester.

### Correctness & validation
- Parsing, target-scoping, junk-rejection, and masking are pure and unit-tested;
  `run()` is exercised end-to-end over an httpx MockTransport, and verified live
  against ransomware.live. 7 new tests (`tests/test_darkweb.py`); 122 tests pass.

Part 2 (planned): Tor `.onion` crawling, paste sweeps, and stealer-log
correlation, under the same masking/scoping guardrails.

---

## [1.15.0] — 2026-07-10

Recursive profile pivoting — the second Phase 4 (identity) module. Turns the
handles found by username enumeration into an identity graph.

### Added
- **Profile pivot** (`intel/people/profile_pivot.py`, `profile_pivot` module):
  parses the profile pages surfaced by username enumeration and mines each for
  the **linked identities** the person publishes — cross-linked handles on other
  platforms, emails, personal domains, and gravatar avatar hashes. An identity
  linked from multiple confirmed profiles scores higher (likely the same person)
  and is flagged.
  - **Pure extractor** (`extract_profile_identifiers`): social-URL →
    `(platform, handle)` with a reserved-path denylist (so nav links like
    `twitter.com/home` aren't mistaken for handles), emails, candidate personal
    domains (registered-domain form, infra + the profile's own domain excluded),
    and gravatar md5 hashes.
  - `ProfilePivotEngine` composes an injectable username enumerator + bounded
    HTTP fetch, with depth/budget/dedup guards mirroring the entity
    `RecursivePivotEngine`. **Default `max_depth 0`** parses the seed's profiles
    only (cheap); each extra hop re-runs the full username enum on discovered
    handles, so deeper pivoting is explicit opt-in (`max_recurse_handles`).
  - Skips dotted / `@`-bearing targets. Emits `linked_identity` per
    handle/email/domain/gravatar (with provenance + cross-link count) and
    `profile_pivot_summary`. Wired into the engine (`-m profile_pivot`), a CLI
    panel, and the web scan form.

### Correctness & validation
- The extractor is pure and unit-tested; `run()` is exercised end-to-end with a
  fake enumerator + an httpx MockTransport (no network).
- 5 new tests (`tests/test_profile_pivot.py`); 115 tests pass.

---

## [1.14.0] — 2026-07-10

Keyless username enumeration — the first Phase 4 (identity) module, opening the
"map a person across the grid" arc (WhatsMyName / Sherlock lineage).

### Added
- **Username enumeration** (`scrapers/username_enum.py`, `username_enum` module):
  checks a handle's presence across ~700 sites with **no API keys**. For each
  site it probes the profile URL and applies that site's detection rule
  (expected status + marker string), then runs a false-positive guard.
  - **Detection rules are vendored** from WhatsMyName
    (`scrapers/data/wmn-data.json`, 719 sites, **CC BY-SA 4.0** with attribution)
    rather than hand-authored — the per-site rules are the error-prone part and
    the community set is tested and maintained.
  - **False-positive guard:** every positive is re-checked against an improbable
    control handle; sites that "match" that are catch-alls and are dropped.
  - Skips dotted / `@`-bearing targets (domains/emails) so a full-spectrum scan
    on a domain never probes the domain string as a username.
  - Emits `username_account` per hit and a `username_enum_summary`
    (by-category counts, profile URLs); a handle found on 10+ sites is flagged
    as a broad-exposure anomaly. Wired into the engine (`-m username_enum`), a
    CLI results panel, and the web scan form.

### Correctness & validation
- Rule evaluation, URL templating, and handle normalisation are pure and
  unit-tested; `run()` is exercised end-to-end over an httpx MockTransport
  (including the false-positive guard) with no network.
- 10 new tests (`tests/test_username_enum.py`); 110 tests pass.

---

## [1.13.0] — 2026-07-10

Document metadata extraction — the final Phase 3 module, completing the
"revive the footprinting canon" arc (FOCA / metagoofil lineage).

### Added
- **Document metadata extraction** (`scrapers/doc_metadata.py`, `doc_metadata`
  module): discovers a domain's public documents via the keyless Wayback CDX
  source, downloads them (streamed, size-capped), and mines embedded metadata
  for internal usernames, software + versions, local/UNC paths, emails, and
  EXIF geolocation. Parsers:
  - **OOXML** (docx/xlsx/pptx + macro variants) — `docProps/core.xml` +
    `app.xml` via stdlib `zipfile`+XML, no external dependency.
  - **PDF** — Info dictionary (literal / hex / UTF-16BE strings, with
    balanced-paren and octal-escape handling) plus the XMP packet.
  - **Images** (JPEG/TIFF) — EXIF via Pillow, including GPS → decimal coords.
  - Emits per-document findings plus username/software/path/email summaries and
    `document_geolocation` (anomaly). Wired into the engine pipeline, the CLI
    `-m doc_metadata` (with a results panel), and the web scan form.

### Scope & correctness (honest by design)
- **PDF parsing covers the uncompressed regions only** — metadata buried in
  object/xref streams or encrypted PDFs is out of scope; a hand-rolled full PDF
  parser would be silently wrong.
- **Legacy OLE (.doc/.xls/.ppt) is not attempted** — it needs a real OLE
  compound-file parser; those extensions are excluded from discovery.
- **Zip-bomb guard bounds *actual* decompressed bytes** (reads a capped stream
  rather than trusting the archive's declared uncompressed size).
- Username aggregation drops software-looking values (e.g. auto-filled app
  names) from person fields.
- 13 new tests (`tests/test_doc_metadata.py`) validating the parsers against
  in-memory OOXML/PDF/EXIF documents; 100 tests pass.

---

## [1.12.0] — 2026-07-10

Stealth port-scan profiles — the final Phase 3 `port_scanner` addition, closing
out the "revive the footprinting canon" work on the scanner. Adds nmap-gated
idle and decoy scans for source-obscured reconnaissance.

### Added
- **Stealth scan profiles** (`scrapers/port_scanner.py`), exposed via
  `--stealth {decoy,idle}` on the CLI `scan` command (with `--zombie` and
  `--decoys`) and threaded through the engine's scan options:
  - **Decoy scan** — `nmap -sS -D <spec> -Pn`; the real probe is hidden among
    decoy source IPs (default `RND:10`, or a caller-supplied `ip1,ME,ip2` spec).
  - **Idle scan** — `nmap -sI <zombie> -Pn`; a zombie-bounced side-channel scan
    that never sends the scanner's own IP to the target.
  - Both deliberately omit `-sV`/`-O`: version/OS probes would originate from
    the real IP (decoy) or are impossible over the idle side channel.
- `build_nmap_command` — pure, unit-tested nmap argv construction.
- CLI port panel renders the stealth engine tag and an "unavailable" notice.

### Correctness & honesty
- **No silent loud fallback:** stealth requests never fall back to the plain
  Python connect scan (which would emit from the real IP). Missing nmap, an
  idle scan without a zombie, or a scan that can't run all emit a
  `stealth_unavailable` finding explaining why — no scan is performed.
- **Downgrade detection:** without raw-packet privileges nmap can silently turn
  `-sS` into a connect scan (real IP, no decoys). The XML's `<scaninfo type>`
  is parsed and a `connect` result is reported as "stealth NOT applied" rather
  than being mislabelled a stealth scan. Verified against real nmap XML
  (`type="syn"` vs `type="connect"`).
- **argv-injection guard** (`_validate_nmap_operand`): zombie/decoy/host
  operands beginning with `-` are rejected so they can't be misparsed as flags.
- **Third-party consent:** an idle scan implicates the zombie host, so the CLI
  requires a separate authorization confirmation naming it.
- 14 new tests (`tests/test_stealth_scan.py`); 87 tests pass.

---

## [1.11.0] — 2026-07-10

Passive OS fingerprinting — a Phase 3 `port_scanner` addition. Until now the
scanner derived the OS only from nmap (`-O`); this adds a p0f-style TCP/IP
fingerprint from the target's SYN-ACK, giving an OS-family signal even when
nmap is absent.

### Added
- **Passive OS fingerprint** (`scrapers/port_scanner.py`):
  - Byte-level `parse_ip_header` / `parse_tcp_header` / `parse_tcp_options` and
    the inference pair `snap_initial_ttl` / `fingerprint_os` — all pure and
    network-free.
  - **TTL→family inference:** a packet's observed TTL is the origin's initial
    TTL minus the hop count, so the initial TTL is the smallest standard value
    (64/128/255) `>=` the observed TTL. 64 → Linux/macOS/BSD/Android, 128 →
    Windows, 255 → network device/Solaris/AIX. The obsolete 32 initial
    (Win9x/ME) is deliberately excluded — an observed TTL of 32 today is far
    more likely a distant Unix host than a dead OS.
  - The family claim is the confident signal; **TCP window / MSS / option shape
    are advisory evidence only** — they nudge confidence but never invent
    version-level precision. An un-bucketable TTL yields no finding (no guess).
  - **SYN-ACK capture** (`_capture_syn_ack`): opens a raw socket, triggers a
    normal handshake, and reads the target's SYN-ACK TTL/window/options.
  - Emits a `passive_os` finding; the CLI port panel shows it when nmap OS is
    absent. Opt-out via `port_scanner.os_fingerprint`.

### Correctness & validation
- Raw capture needs `CAP_NET_RAW`; without it `_capture_syn_ack` returns `None`
  (clean skip, no false OS guess). Verified that `IP_RECVTTL` yields no
  ancillary data on TCP streams and that raw sockets are denied unprivileged —
  so live capture can't run in the sandbox, and the error-prone parsing +
  inference is validated **offline against crafted Linux/Windows SYN-ACK
  packets** (byte-built in the tests): option parsing, malformed-option
  termination, TTL bucketing, and end-to-end family inference.
- 9 new tests (`tests/test_os_fingerprint.py`); 73 tests pass.

---

## [1.10.0] — 2026-07-10

Classic DNS enumeration — the second Phase 3 "revive the footprinting canon"
release. `dns_recon` already pulled records, attempted zone transfer, and
brute-forced subdomains; this adds three techniques that surface names and
misconfigurations those passes miss, all authorised-active.

### Added
- **DNSSEC NSEC zone-walking** (`_nsec_walk`) — NSEC-signed zones leak every
  name via the NSEC `next` chain even when AXFR is refused. Sends non-recursive
  DNSSEC queries against an authoritative NS and follows the chain to its
  wrap-to-apex. Detects **NSEC3** (hashed) and reports it rather than pretending
  to walk it. Emits `nsec_zone_walk` (anomaly) and re-emits each in-zone name as
  a `subdomain` finding so it feeds the pivot + takeover engines.
- **PTR netblock sweep** (`_ptr_sweep`) — reverse-resolves the entire /24 around
  the target's A record (concurrency-bounded), surfacing co-hosted infrastructure.
  Emits `ptr_sweep_summary`; co-hosted names within the registered domain are
  re-emitted as `subdomain` findings for the pivot.
- **DNS cache snooping** (`_cache_snoop`) — non-recursive (RD=0) probes of the
  domain's nameservers for a set of common third-party domains. A cached answer
  means the server is cache-snoopable, revealing what its users recently
  resolved. Emits `dns_cache_snoop` (anomaly, open-resolver/misconfig tags).
- CLI `◈ DNS INTELLIGENCE` panel lines for NSEC walk, PTR sweep, and cache snoop.

### Correctness & validation
- Live NSEC/cache-snoop queries can't run in the sandbox (outbound UDP/53 is
  blocked), so the error-prone logic is unit-tested against crafted records: the
  pure walk driver `nsec_walk_names` (wrap-to-apex, loop, dead-end, and
  out-of-zone termination), NSEC/NSEC3 record parsing, and `/24` host expansion.
  The walk driver is bounded (`max_steps`) and network-free by construction.
- 6 new tests (`tests/test_dns_enum.py`); 64 tests pass.

---

## [1.9.0] — 2026-07-08

Classic enumeration release — the first of the Phase 3 "revive the footprinting
canon" modules. PhantomSignal already flagged ports 25/139/445/161 as dangerous
but never enumerated them; this adds correct, active enumeration for the two we
can implement from scratch with confidence.

### Added
- **Service enumeration** (`scrapers/service_enum.py`, `service_enum` module):
  - **SMTP (port 25)** — `VRFY`/`EXPN` username enumeration with an automatic
    `RCPT TO` fallback when `VRFY` is disabled, plus an **open-relay** check
    (a foreign `MAIL FROM` + foreign `RCPT TO` both accepted). For a domain
    target the MX host is resolved and probed. Emits `smtp_users` (valid
    mailboxes, flagged as anomalies) and `smtp_open_relay`.
  - **SNMP (port 161/udp)** — community-string enumeration via a hand-built
    SNMPv1 `GetRequest` for `sysDescr.0`; a valid community leaks the device
    description. Tries a small default/common community list and stops at the
    first hit. Emits `snmp_community` (with a `default-community` tag for
    `public`/`private`).
  - Wired into the engine pipeline, the CLI `--modules service_enum` with a
    dedicated results panel, and the web scan form (module card + result
    rendering for all three finding types).

### Correctness & validation
- The SNMP `GetRequest` encoder is validated **byte-for-byte** against the
  canonical `sysDescr.0` / community `public` reference packet, and the response
  parser round-trips a `GetResponse` and rejects `error-status`/non-SNMP input.
- The SMTP conversation (banner → `EHLO` → `VRFY`/`RCPT` → relay probe → `QUIT`)
  is verified end-to-end against an in-memory server: `VRFY` enumeration isolates
  valid users and open-relay detection fires correctly.
- Response classification and packet encode/parse are pure functions; **7 unit
  tests** added (52 → **58 total**).

### Deferred (deliberately)
- **NetBIOS/SMB null-session enumeration** (139/445) is *not* included. A correct
  implementation needs a real SMB stack (impacket); a hand-rolled one would be the
  kind of silently-wrong protocol code this project refuses to ship (see the JARM
  notes in v1.8.0). It is a tracked follow-up.

### Operational
- `service_enum` performs **active** enumeration (SMTP `VRFY`/`RCPT` probes, SNMP
  community guesses). Run it only against systems you are authorised to test.

---

## [1.8.0] — 2026-07-08

JARM release. Adds a validated, from-scratch **active TLS-stack fingerprint** to
the `infra_pivot` module, replacing the JARM that was deliberately deferred in
v1.7.0 rather than shipped incorrect. This entry is intentionally detailed: JARM
is an algorithm that is easy to get *almost* right and impossible to debug by eye,
so the failure modes are documented here as much as the feature.

### Added
- **JARM active TLS fingerprinting** (`scrapers/jarm.py`). Sends ten deliberately
  varied TLS Client Hellos and fuzzy-hashes the server's responses into the
  standard 62-character JARM. Two servers with the same TLS stack + configuration
  produce the same fingerprint, making it a high-signal infrastructure pivot.
  - Integrated into the `infra_pivot` module: emits a `jarm_fingerprint` result
    and pivots siblings via Shodan `ssl.jarm:<hash>`. Surfaced in the CLI
    `infra_pivot` panel and the web results view.
  - The ten-probe matrix varies TLS version (1.1/1.2/1.3), cipher-list ordering
    (forward / reverse / top-half / bottom-half / middle-out), GREASE injection,
    rare-ALPN sets, and extension ordering — the server's *disagreements* across
    these are the fingerprint.
  - Pure packet-construction and hashing functions are split from the socket
    driver; **7 unit tests** cover cipher reordering, hash encoding, Client Hello
    framing, and Server Hello parser guards. Total suite: **51 tests**.
- **Technical documentation** under `docs/jarm/` — a from-the-inside-out
  walkthrough written because this was built from scratch:
  - `README.md` — what JARM is and why it uses deliberately odd handshakes.
  - `01-tls-primer.md` — the TLS record layer, Client/Server Hello framing, cipher
    suites, extensions, and GREASE (just enough to follow the rest).
  - `02-jarm-algorithm.md` — the ten probes as a matrix, what each axis tests, and
    the token → raw → hash data flow.
  - `03-clienthello-anatomy.md` — byte-by-byte Client Hello construction with
    length-field maps and the exact extension set/order.
  - `04-serverhello-and-hash.md` — Server Hello field offsets and the 62-char
    fuzzy-hash assembly (30 cipher/version chars + 32 SHA-256 chars).
  - `05-implementation-and-validation.md` — code map, the three silent bugs, and
    the validation method.

### Correctness notes (why this is "done right")
The initial from-scratch attempt failed three ways — one loud, two silent — and
all three are the kind that pass a casual "it runs and returns a hash" check:

1. **Malformed Client Hello (loud).** A fabricated extension, wrong bytes for
   `ec_point_formats` / `signature_algorithms`, and four missing extensions
   (`extended_master_secret`, `max_fragment_length`, `renegotiation_info`,
   `psk_key_exchange_modes`) caused servers to reject every probe with a TLS
   `decode_error` alert → an all-zero fingerprint. Fixed by rebuilding the exact
   extension set/order; the verification signal is the server switching from an
   alert to a Server Hello (9/10 probes for a strict server, with the TLS-1.3
   contradiction probe legitimately returning `handshake_failure`).
2. **`supported_versions` sent unconditionally (silent).** The extension must be
   emitted only on TLS-1.3 or `1.2_SUPPORT` probes; sending it on the
   `NO_SUPPORT` probes changes what they ask and drifts the fingerprint while the
   packets still parse.
3. **Hashing with the wrong cipher table (silent).** `cipher_code` must index
   JARM's separate **value-sorted** cipher table, not the offer-order list used in
   the Client Hello. Using the wrong table yields a deterministic, well-formed,
   62-char hash that matches no other JARM implementation — defeating the entire
   purpose (cross-tool `ssl.jarm:` pivoting).

**Validation.** With the free-tier Shodan key unable to run `ssl.jarm:` searches,
correctness was established two ways: (a) diffing cipher lists, `cipher_mung`,
extension bytes/order, Server Hello offsets, and the hash functions against the
canonical Salesforce reference; and (b) reproducing Google's publicly documented
fingerprint prefix `27d40d40d29d40d1dc42d43d00041d…` byte-for-byte.

### Operational
- JARM is **active** — it opens ten TCP connections to port 443. Run it only
  against authorised targets. The blocking socket work runs in an executor so it
  doesn't stall the async pipeline.

---

## [1.7.0] — 2026-07-08

Infrastructure-pivot release, completing the Phase 2 "modern recon sources" set.

### Added
- **Infrastructure pivot** (`scrapers/infra_pivot.py`, `infra_pivot` module) —
  fingerprints a target and pivots to sibling infrastructure two ways:
  - **Favicon hash** — Shodan's MurmurHash3-of-base64 favicon hash,
    reimplemented in pure Python (no native `mmh3` dependency; verified
    byte-for-byte against the reference). Pivots via Shodan `http.favicon.hash:`.
  - **TLS certificate** — leaf-cert SHA-256 fingerprint plus Subject Alternative
    Names via the stdlib `ssl` module. SANs are emitted as subdomains that feed
    the recursive pivot and takeover detector; pivots via Shodan
    `ssl.cert.serial:`. Sibling IPs from either pivot feed the graph.
- CLI `--modules infra_pivot` with a result panel; a web scan-form card and
  favicon/cert/sibling results rendering.

### Notes
- An active **JARM** TLS-stack fingerprint was scoped for this release but
  deferred: a from-scratch port produced malformed TLS Client Hellos, and a
  silently-wrong fingerprint is unacceptable in a security tool. The correct
  stdlib TLS-certificate pivot ships as the TLS-axis substitute; JARM will land
  later via a vetted reference implementation with published test vectors.
- Test suite grew to 44 tests (added MurmurHash3 vectors, favicon hashing,
  favicon-URL resolution, cert fingerprinting, and SAN scoping).

---

## [1.6.0] — 2026-07-07

Content-mining release. Two new passive recon modules extend the attack-surface
pipeline by mining what a target already exposes — its JavaScript and its
historical URLs — and feed the discoveries back into the v1.5.0 pivot, takeover,
and signature engines.

### Added
- **JavaScript secret & endpoint mining** (`scrapers/js_miner.py`, `js_mine`
  module) — fetches a target's page plus every linked and inline script and mines
  the JavaScript for leaked secrets (AWS/Google/Slack/GitHub/Stripe/Twilio/
  SendGrid keys, private keys, JWTs, and entropy-gated generic key/token
  assignments) and API endpoints (absolute URLs + root-relative API paths, with
  XML-namespace and asset-extension noise filtered). Secrets are **masked** in
  output so raw credentials are never written to the database or exports. Secret
  detectors mirror the exposed-secret signature templates.
- **Archive URL mining** (`scrapers/archive_miner.py`, `archive_mine` module) —
  passive historical URL discovery (gau/waybackurls lineage) from keyless sources
  (Wayback CDX, AlienVault OTX, URLScan) gathered concurrently with graceful
  degradation. Scopes URLs to the target, flags sensitive files/paths and
  parameterised endpoints, inventories query parameters, and emits the distinct
  historical subdomains seen across captures — which feed the recursive pivot and
  takeover detector.

### Changed
- **CLI `--modules`** now accepts `js_mine` and `archive_mine`, each with a
  dedicated result panel; both modules also appear as cards on the web scan form
  with tailored results rendering.
- **Test suite** grew to 39 tests (added JS-miner extraction/detection/entropy
  and archive parse/scope/classify coverage).

---

## [1.5.0] — 2026-07-07

Attack-surface pipeline release. PhantomSignal moves from a single-pass API
aggregator toward a continuous attack-surface platform: discovered assets now
feed back in automatically, exposures are matched by data-driven signatures, and
subdomain discovery/takeover detection land as first-class modules. All new
capability is opt-in and the default single-pass behaviour is unchanged.

### Added
- **Recursive entity-graph pivoting** (`intel/pivot.py`) — the orchestrator can now
  feed discovered IPs, subdomains, and emails back in as new targets via a
  breadth-first `RecursivePivotEngine` with dedup, depth, entity-budget, and
  eTLD+1 scope guards. Opt in through `run()` options (`recursive`, `max_depth`,
  `allow_cross_domain`). Turns the aggregator into a SpiderFoot-class expander.
- **Signature engine** (`intel/signatures/`) — a Nuclei-style YAML template engine
  with two modes: `match` (word/regex/keyword matchers over aggregated results)
  and `dork` (GHDB queries rendered scoped to the target). Ships GHDB
  config/secrets and exposed-panel dork packs plus subdomain-takeover and
  exposed-VCS/cloud-key match templates. Enable via the `signatures` option.
- **Passive subdomain enumeration at scale** (`scrapers/subdomain_enum.py`) — new
  `subdomain_enum` module. Keyless multi-source gathering (crt.sh, HackerTarget,
  AlienVault OTX passive DNS, Anubis) with graceful per-source degradation,
  permutation generation, wildcard-DNS detection + filtering, and concurrent
  resolve-validation. Emits results carrying A records and CNAMEs.
- **Active subdomain-takeover detection** (`scrapers/takeover.py`) — new `takeover`
  module. A can-i-take-over-xyz-style fingerprint DB plus active HTTP-body and
  NXDOMAIN confirmation, producing graded verdicts (vulnerable / candidate /
  suppressed) tuned to minimise false positives.
- **Attack-surface pipeline controls in the web UI** — the scan form gains a
  Recursive Pivot toggle (with depth + cross-domain sub-options) and a Signature
  Engine toggle, plus Subdomain Enum and Takeover Detect module cards. Results
  render dork findings as clickable searches, and signature/takeover findings
  with severity badges.
- **Test suite** (`tests/`) — the repository's first automated tests: 33 tests
  covering pivot entity-extraction and guards, signature matching/dork scoping,
  subdomain-enum parsing and wildcard filtering, and the takeover grading matrix.

### Changed
- **Tagline** — replaced *"See everything. Leave no trace."* with **"Map the
  surface. Own the signal."** across the CLI banner, README, homepage, HTML
  export footer, and ASCII-art scripts; the old line was contradicted by
  `ROBOTSTXT_OBEY` and a self-identifying User-Agent.
- **CLI `--modules`** now accepts `subdomain_enum` and `takeover`, with dedicated
  result panels for each.
- Added a `docs/assets` project gravatar and `scripts/render_gravatar.py`.

---

## [1.4.3] — 2026-06-10

### Fixed
- **Quick probe intel coverage** — `IntelOrchestrator._get_applicable_apis` was silently skipping applicable APIs for several target types. Username targets matched zero intel APIs (no branch existed for them). Email targets missed threat-intel, breach, and people-category sources. Domain targets missed email-category APIs (Hunter.io email discovery). IP targets missed dark-web sources (Intelligence X paste/leak search).

  Updated category sets per target type:
  - **IP** — `network | threat_intel | geolocation | vulnerability | dark_web`
  - **Email** — `email | breach | threat_intel | people`
  - **Domain** — `domain | threat_intel | email`
  - **Username** — `social | people` *(new branch)*

  All individual API implementations retain their own target-type guards and return `[]` gracefully for unsupported input, so no new noise is introduced.

---

## [1.4.2] — 2026-06-06

### Fixed
- Export commands now work immediately after install — `ExportManager`, `config`, and the `export` CLI command all default output to `/tmp` instead of `./exports`, preventing permission errors for users who haven't configured an output directory. Override with `PHANTOMSIGNAL_EXPORT_DIR` env var or `--output`.
- `RuntimeWarning: coroutine was never awaited` printed on every scan when modules were excluded from the pipeline — `_build_pipeline` now uses lazy factories so coroutines are only created for modules that will actually run.
- `scan --output` flag now treated as a directory path (not a file path), matching the documented behaviour.

---

## [1.4.1] — 2026-06-06

### Changed
- README updated to reflect v1.4.0 features — What's New section, API integrations table (46+ sources), architecture count

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

[Unreleased]: https://github.com/getphantomsignal/phantomsignal/compare/v1.4.2...HEAD
[1.4.2]: https://github.com/getphantomsignal/phantomsignal/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/getphantomsignal/phantomsignal/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.3.3...v1.4.0
[1.3.3]: https://github.com/getphantomsignal/phantomsignal/compare/v1.3.1...v1.3.3
[1.3.1]: https://github.com/getphantomsignal/phantomsignal/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.5...v1.3.0
[1.2.5]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/getphantomsignal/phantomsignal/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/getphantomsignal/phantomsignal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/getphantomsignal/phantomsignal/releases/tag/v1.0.0
