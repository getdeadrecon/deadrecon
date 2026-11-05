# DeadRecon — User Guide

> **Legal reminder:** Only scan targets you own or have explicit written permission to test. Refer to the [Legal & Ethics](../README.md#️-legal--ethics) section in the README before proceeding.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [The Web Interface](#2-the-web-interface)
3. [Launching a Scan](#3-launching-a-scan)
4. [Usage Scenarios](#4-usage-scenarios)
   - [Scenario A — Website Security Audit](#scenario-a--website-security-audit)
   - [Scenario B — IP / Server Reconnaissance](#scenario-b--ip--server-reconnaissance)
   - [Scenario C — Domain Intelligence](#scenario-c--domain-intelligence)
   - [Scenario D — People Intelligence (Profiler)](#scenario-d--people-intelligence-profiler)
   - [Scenario E — Bug Bounty Recon](#scenario-e--bug-bounty-recon)
   - [Scenario F — Covert Recon (Low-and-Slow)](#scenario-f--covert-recon-low-and-slow)
5. [Configuring API Keys](#5-configuring-api-keys)
6. [Reading Results](#6-reading-results)
7. [Exporting Intel](#7-exporting-intel)
8. [CLI Usage](#8-cli-usage)
9. [Troubleshooting](#9-troubleshooting)
   - [Linux](#linux)
   - [macOS](#macos)
   - [Windows](#windows)
   - [Docker](#docker)

---

## 1. Getting Started

### Installation (Manual)

```bash
# Requires Python 3.10+
git clone https://github.com/getdeadrecon/deadrecon
cd deadrecon
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

### Installation (Docker)

```bash
git clone https://github.com/getdeadrecon/deadrecon
cd deadrecon
docker-compose up -d
```

Open **http://localhost:5000**.

### Signing in

The console has one operator account. On first run the server prints a one-time
setup token; enter it at **http://localhost:5000** to create the account. On
Docker, read it with `docker logs deadrecon`.

| Task | Command |
|------|---------|
| Create the account without the browser, or reset a forgotten password | `deadrecon set-password` |
| Create a REST API token (revokes the previous one) | `deadrecon api-token` |

Run these with the same working directory or `DEADRECON_DB_URL` as the server,
so they use the same database. On Docker, use `docker exec -it deadrecon deadrecon set-password`.

Docker publishes the console on loopback only. To reach it from other machines,
put it behind a TLS reverse proxy and set:

| Variable | Value |
|----------|-------|
| `DEADRECON_SECURE_COOKIES` | `true` |
| `DEADRECON_ALLOWED_ORIGINS` | The public URL, for example `https://recon.example.com`. Separate several with commas. |

### What changes when a proxy is configured

With a proxy configured, these keep your IP away from the target and your local DNS resolver:

- DNS lookups use DNS-over-HTTPS through the proxy (`scraper.doh_url` sets the provider).
- Zone transfers, direct nameserver queries, and raw TLS and JARM probes are skipped, so those results won't appear.

The Go tools are adjusted when proxied. `nuclei` runs HTTP templates only, because its other protocols bypass the proxy, and still asks your local resolver for the target's name; the scan's attribution report says so. `subfinder` skips its `crtsh` source, which connects directly. `tlsx` and `naabu` can't use a proxy, so they're reported as attributable.

Port scans, SMTP probes and WHOIS lookups still connect directly. The scan's attribution report marks them as attributable.

### First-run checklist

| Step | Action |
|------|--------|
| 1 | Open the web UI at `http://127.0.0.1:5000` |
| 2 | Navigate to **Integrations** (⚙ in nav bar) and add at least one API key |
| 3 | Go back to the **Dashboard** |
| 4 | Use **Quick Scan** or **New Scan** to start your first scan |

---

## 2. The Web Interface

### Navigation

| Nav | What it does |
|-----|--------------|
| **Dashboard** | Overview, live feed, data-source status, and a Quick Scan box |
| **New Scan** | Full scan configuration form |
| **Scans** | All past and active scans |
| **Profiler** | Person / email / username lookup |
| **Integrations** | API key management |


### Live Feed

The **LIVE FEED** terminal on the dashboard streams real-time events from any active scan via WebSocket. Events are colour-coded:
- **Cyan** — system/connection messages
- **Green** — successful findings
- **Yellow/Orange** — warnings
- **Red** — errors or high-severity findings

---

## 3. Launching a Scan

### Quick Scan (dashboard)

The fastest way to start — enter a target in the **QUICK SCAN** box on the dashboard. This runs all five default modules (`dns_recon`, `port_scan`, `tech_detect`, `api_hunt`, `intel`) with the quick profile. Results appear under **Scans** as modules finish.

### Full Scan (New Scan page)

1. Navigate to **New Scan**
2. Enter your target (domain, IP, URL, email, or username)
3. Choose a **Scan Profile**:

| Profile | What it changes |
|---------|-----------------|
| **Quick** | On the CLI, crawl depth 2 instead of 3. In the console, nothing beyond the label |
| **Standard** | The default |
| **Deep** | Currently the same as Standard |
| **Covert** | Uses `paranoid` pacing and skips modules that connect directly from your IP |

The profile doesn't choose modules or ports. Set those with **Modules** and **Advanced Options**, or `--modules` on the CLI. How long a scan takes depends on those choices and on the target.

4. Toggle individual **Modules** on/off as needed
5. Adjust **Advanced Options** (crawl depth, port profile, robots.txt respect)
6. Click **Start Scan**

You are redirected to the live results page where findings stream in as they're discovered.

---

## 4. Usage Scenarios

### Scenario A — Website Security Audit

**Goal:** Assess the security posture of a web application you own.

**Recommended settings:**
- Target: `https://yoursite.com`
- Profile: **Standard**
- Modules: DNS Recon ✓, Port Scanner ✓, Tech Detector ✓, API Hunter ✓, Web Crawler ✓
- Evasive mode: off

**What DeadRecon will find:**
- Open ports and exposed services (admin panels, staging, APIs)
- Technology stack (CMS version, frameworks, CDNs, WAF presence)
- Missing security headers (CSP, X-Frame-Options, HSTS)
- Exposed API endpoints, GraphQL introspection, `.env` files
- Email addresses and internal links harvested from crawl
- Threat intelligence from VirusTotal, Shodan, AbuseIPDB (if keys configured)

**Interpreting the Risk Score:**
- **0–25 CLEAN** — minimal exposure, good security posture
- **26–50 ELEVATED** — some findings worth reviewing
- **51–75 HIGH** — significant issues, remediation recommended
- **76–100 CRITICAL** — urgent issues, active risk

---

### Scenario B — IP / Server Reconnaissance

**Goal:** Enumerate open services and threat history for an IP address.

**Recommended settings:**
- Target: `192.168.1.100` (or public IP)
- Profile: **Standard**
- Modules: Port Scanner ✓, DNS Recon ✓, Intel APIs ✓
- Port Profile: **Top 1000** or **Full range (65535)** for thorough coverage. Port scans over the full range can hit the 5-minute module limit

**What DeadRecon will find:**
- All open TCP ports with service/version from nmap (`-sV`) and banner grabbing — falls back to pure-Python async prober when nmap unavailable
- **OS fingerprint** — detected automatically via nmap `-O` and shown in the port panel footer (e.g. "Linux 5.15 [95%]")
- Reverse DNS and PTR records
- ASN, ISP, geolocation data (IPInfo — no key required)
- CVE matches via Shodan (if API key set)
- AbuseIPDB confidence score and report history
- VirusTotal passive DNS, malware history
- GreyNoise classification (scanner, benign, unknown)

**Tip:** nmap is used automatically when present. On Kali/Parrot it's pre-installed. On macOS install via `brew install nmap`; on Windows via the nmap.org installer. Without nmap the async TCP scanner still runs — you just won't get version strings or OS detection.

---

### Scenario C — Domain Intelligence

**Goal:** Map the full attack surface of a domain.

**Recommended settings:**
- Target: `example.com`
- Profile: **Standard**
- Modules: DNS Recon ✓, Tech Detector ✓, Intel APIs ✓, Web Crawler ✓
- Crawl depth: 3

**What DeadRecon will find:**
- All DNS records (A, AAAA, MX, NS, TXT, SOA, CAA)
- Zone transfer vulnerabilities
- Subdomain enumeration via brute-force wordlist + certificate transparency (crt.sh)
- SPF, DMARC, DKIM configuration issues (email spoofing risk)
- WHOIS registrant data and expiry
- Co-hosted domains and shared infrastructure
- SecurityTrails historical DNS (if API key set)

**Tip:** For maximum subdomain coverage configure both a **SecurityTrails** key and enable certificate transparency — these two sources together find far more subdomains than brute-force alone.

---

### Scenario D — People Intelligence (Profiler)

**Goal:** Aggregate publicly available information about a person, email address, or online identity.

**Navigate to:** **Profiler** (◉ in the nav bar)

**Input types supported:**
- Full name + optional location/employer
- Email address
- Username / handle
- Phone number

**What DeadRecon aggregates:**
- Public social media profiles (GitHub, GitLab, Reddit, Mastodon, Keybase, and — with keys — Twitter/X, LinkedIn via Clearbit)
- Breach exposure via **XposedOrNot (no key required)**, HaveIBeenPwned (HIBP key), and Intelligence X
- Real name + email harvested from public **GitHub / GitLab commits**
- Structured biography for named people via **Wikidata** (DOB, official site, linked socials)
- Fediverse resolution via **WebFinger**; US employer/occupation via **openFEC**; company roles via **OpenCorporates**
- Phone metadata — carrier, region, line-type — **offline** via libphonenumber (no key, no network)
- People-search aggregator data (Pipl, FullContact, Spokeo, WhitePages — keys required)
- Email validity and domain reputation; associated accounts and aliases

**Works with zero API keys:** a full tier of the sources above is keyless, so the Profiler returns a useful baseline on a fresh install. Add keys to deepen it.

**Every run is saved as a scan.** A Profiler search is persisted as a `people_intel` scan (with a linked shadow profile), so it appears under **Scans** with history, a categorised **People & Identity** summary, and export. Use the **View in Scans** button on the results page to jump there. From the CLI, `deadrecon profile …` saves the same way and prints the scan id.

**OPSEC:** the keyless identity sources use your proxy pool when one is configured, and their lookups are counted in the scan's attribution surface. Other API sources, including keyed providers, connect directly unless Tor is on, and the report marks them as attributable. The offline phone source adds nothing to your footprint.

**Privacy note:** The Profiler only queries publicly available data sources and licensed APIs. Configure only the APIs you have a legitimate subscription to. GDPR and CCPA restrictions apply — see [Legal & Ethics](../README.md#️-legal--ethics).

---

### Scenario E — Bug Bounty Recon

**Goal:** Efficiently enumerate in-scope assets for a bug bounty programme.

**Workflow:**

1. **Quick Scan** each root domain to identify live assets
2. For live targets, run a **Standard** scan with all modules enabled
3. Focus review on:
   - API Hunter results (`/api/`, `/graphql`, admin panels)
   - High/Critical severity findings
   - Exposed `.git`, `.env`, `backup` paths in web crawl
   - Subdomains pointing to unclaimed cloud services (subdomain takeover candidates)
4. Export results as **JSON** for integration with your notes / Burp Suite

**Useful API keys for bug bounty:**
- **Shodan** — CVE and banner data
- **SecurityTrails** — historical DNS for subdomain discovery
- **URLScan.io** — passive screenshot and DOM analysis
- **VirusTotal** — passive DNS and URL history

**Tip:** Use the **Covert** profile if the programme's scope rules require low-noise recon. Enable **Respect robots.txt** to avoid accidental out-of-scope crawling.

---

### Scenario F — Covert Recon (Low-and-Slow)

**Goal:** Perform recon with the lowest possible noise and detection footprint.

**Settings:**
- Profile: **Covert**
- Enable **Evasive (low & slow)** toggle in Advanced Config
- Respect robots.txt: **on**
- Crawl depth: **1** (surface only)

**What the Covert profile does:**
- Paces requests with the `paranoid` stealth profile: at most 2 at once per host, at least 1.5 seconds apart, plus 0.5–3 seconds of jitter
- Keeps one browser identity per target
- Skips modules that would connect directly from your IP, such as port scans, and lists them in the report

Covert doesn't hide your IP by itself. Add Tor or a proxy for that.

**Tor:** click the **🧅 Tor** button at the top of any page. That's all. DeadRecon starts Tor, shows its progress, and turns the button purple when it's confirmed working. Click it again to turn Tor off. The setting is remembered across restarts.

On the CLI, add `--tor` to a scan, or run `deadrecon tor on` to keep it on. In Docker, Tor is built into the image, and `docker-compose --profile covert up -d` also turns it on.

DeadRecon uses Tor in this order:
1. The service you configured, if you set `DEADRECON_TOR_HOST`, `DEADRECON_TOR_PORT` or `scraper.tor_port`. Nothing else is tried if it's down.
2. Tor already running on port 9050, or Tor Browser on port 9150.
3. A `tor` program installed on this machine.
4. The official Tor Expert Bundle, downloaded once from torproject.org into `~/.deadrecon/tor` and checked against a pinned SHA-256 hash.

Tor started by DeadRecon listens only on this machine, and stops when DeadRecon stops. Automatic start doesn't configure bridges, so where Tor is blocked, run your own Tor with bridges and point `DEADRECON_TOR_HOST` at it.

With Tor on:
- **Each scan first confirms it's on Tor** with `check.torproject.org`. If Tor is still starting, the scan waits for it. If Tor can't be confirmed, the scan stops with an error before contacting the target. To skip this check, set `scraper.tor_verify` to `false`; a Tor outage then shows up as failed requests rather than a stopped scan.
- **TLS impersonation and `quiet` pacing turn on automatically**, unless you've chosen `paranoid`.
- **All HTTP and DNS use Tor**, including keyed APIs, alert webhooks and proxy-list downloads. Different targets use different circuits. If a target blocks a Tor exit, the scan moves to a new circuit.
- **WHOIS lookups use RDAP over HTTPS**, because WHOIS itself can't go through Tor.
- **Modules that would bypass Tor are skipped** and listed in the report: `port_scan`, `port_scan_fast`, `service_enum`, `tls_fingerprint` and `vuln_scan`. `vuln_scan` is included because `nuclei` connects directly to some hosts and asks your local DNS resolver for the target's name.
- **Scans are slower.** Timeouts are longer, and many sites block Tor exits, so some modules can find less than they would directly.

`.onion` targets need Tor. Only `web_crawl`, `web_crawl_fast`, `tech_detect`, `api_hunt` and `js_mine` run against them, because the others would send the address to third parties. A target without a scheme uses `http://`.

Check your setup on the **Identity** page, which shows your exit IP and whether Tor is confirmed.

**What the grade means under Tor:** a Tor scan can still grade **Partial**, because modules that don't use a browser TLS fingerprint rule out **Masked**. That doesn't mean traffic went direct. In packet captures of real Tor scans, nothing left outside the Tor connection, whether the grade was Partial or Masked. The report says when that's the reason.

**Stealth profile + proxy pool (Settings → Scan Settings):**
- **Stealth profile** — `off` / `quiet` / `paranoid` controls per-host adaptive pacing, sticky browser identity, JA3/JA4 impersonation, and WAF-aware backoff.
- **Rotating proxy pool** — one egress per host (`sticky`) or a fresh egress per request (`every`); burned proxies are benched and rotated automatically.
- **Seed the pool in one click** — pull from a curated free feed (ProxyScrape, TheSpeedX, monosans, Proxifly), paste a custom list URL, or **upload a list file** (`ip:port`, `scheme://ip:port`, `user:pass@ip:port`, or `ip:port:user:pass`, one per line).
- **These settings persist** across restarts (`~/.deadrecon/config.yaml`).

> ⚠️ Free public proxies are unvetted and often dead or hostile (a proxy operator can read/modify unencrypted traffic). Treat them as blend-in cover for low-sensitivity recon — pair with HTTPS and prefer your own egress for anything sensitive.

**Posture at a glance:** the navbar shows a **STEALTH / PARTIAL / DIRECT** chip reflecting your current profile + proxy configuration, and every scan ends with an attribution-surface grade of what actually leaked.

**Tip:** Covert scanning significantly increases scan duration. Plan for 30–90 minutes on a moderately sized target, and longer over Tor.

---

## 5. Configuring API Keys

Navigate to **Integrations** (⚙ in the nav bar).

### Priority keys (highest value, free tiers available)

| API | Free Tier | What It Adds |
|-----|-----------|--------------|
| **Shodan** | 100 queries/month | CVEs, banners, open ports from passive scans |
| **VirusTotal** | 500 lookups/day | Malware, passive DNS, URL reputation |
| **AbuseIPDB** | 1,000/day | IP abuse reports, confidence scores |
| **IPInfo** | 50,000/month | ASN, geolocation, ISP |
| **SecurityTrails** | 50/month | Subdomain history, historical DNS |
| **HaveIBeenPwned** | Paid (cheap) | Breach exposure for emails |
| **Hunter.io** | 25/month | Email discovery from domains |

### Setting keys via environment variables

Keys entered in the Integrations UI are stored in the local SQLite database. For production or Docker deployments, prefer environment variables:

```bash
export SHODAN_API_KEY="your-key"
export VIRUSTOTAL_API_KEY="your-key"
export ABUSEIPDB_API_KEY="your-key"
export IPINFO_TOKEN="your-key"
export HUNTER_API_KEY="your-key"
export HIBP_API_KEY="your-key"
export SECURITYTRAILS_API_KEY="your-key"
```

Or add them to a `.env` file in the project root (Docker Compose picks this up automatically).

---

## 6. Reading Results

### Results page layout

After a scan completes, the results page shows:

- **Meta strip** — target, profile, duration, result count, Risk Score, threat level
- **Tabs** — ALL · per-module tabs · ANOMALIES (auto-filtered)
- **Type-aware result cards** — each result type renders its key data as structured output rather than raw JSON: open ports show port/service/version/banner/risk in one row; DNS records display as a labelled table; email security shows SPF/DMARC/spoofable status; security posture shows grade A–F; IP geolocation shows city/ASN/TOR/VPN flags; and so on. Click any card to expand it.
- **Export panel** — download in any supported format

### Severity levels

| Level | Colour | Meaning |
|-------|--------|---------|
| **CRITICAL** | Red | Immediate risk — active exploit, exposed credentials |
| **HIGH** | Orange/Red | Significant vulnerability requiring prompt remediation |
| **MEDIUM** | Yellow | Notable finding, assess and plan remediation |
| **LOW** | Green | Informational, minor exposure |
| **INFO** | Blue/Dim | Context data, no direct risk |

### Risk Score breakdown

The Risk Score (0–100) is a weighted composite:
- Open high-risk ports (admin panels, databases) — high weight
- Critical/High severity findings — high weight
- Missing security headers — medium weight
- Exposed subdomains and services — medium weight
- Breach exposure and threat intel flags — variable weight

---

## 7. Exporting Intel

From any scan results page, click **↓ EXPORT INTEL** and choose a format:

| Format | Best For |
|--------|----------|
| **JSON** | Programmatic processing, importing to other tools |
| **HTML** | Shareable self-contained styled report |
| **PDF** | Formal client deliverable |
| **CSV** | Spreadsheet analysis in Excel / Google Sheets |
| **XLSX** | Excel workbook with multiple sheets per module |
| **STIX 2.1** | Threat intelligence sharing (SOC / SIEM integration) |
| **XML** | Legacy system import |
| **Markdown** | Documentation, GitHub issues, Notion |

### Encrypting exports

All formats support **AES-256-GCM encryption**. Check the **Encrypt** checkbox before exporting and set a passphrase. The encrypted file includes a nonce and authentication tag — decryption requires DeadRecon or a compatible AES-256-GCM implementation.

---

## 8. CLI Usage

```bash
# Activate virtual environment first
source .venv/bin/activate

# Quick scan — renders DNS, port, tech, API, intel panels in terminal
deadrecon scan example.com --profile quick

# IP recon — nmap version+OS detection, 99-port default, GeoIP
deadrecon scan 192.168.1.1 --type ip_recon

# HTML report in a folder you choose
deadrecon scan example.com --format html --output ./reports

# Choose modules: repeat the flag or separate names with commas
deadrecon scan example.com -m dns_recon -m tech_detect
deadrecon scan example.com -m dns_recon,tech_detect,web_crawl

# Over Tor: starts Tor for you, and stops if it can't confirm it
deadrecon scan example.com --tor

# Compare the two most recent completed scans of a target
deadrecon diff example.com

# Export a saved scan again
deadrecon export <scan-id> --format xlsx

# People intelligence
deadrecon profile --email target@example.com --first-name John --last-name Doe

# Show API sources, whether each is configured, and recent scans
deadrecon status

# Check version
deadrecon --version
```

**CLI output (v1.3.0+):** After the scan completes, results are rendered as named Rich panels — one per active module — rather than a flat table. Each panel extracts the key fields from result data: the port panel shows PORT/SERVICE/PROTO/VERSION/BANNER/RISK with dangerous ports highlighted; the DNS panel shows resolved IPs, MX/NS/TXT records, subdomains, and SPF/DMARC status; the tech panel shows detected stack, security header grade, and TLS info; anomalies appear in a separate red-bordered callout. The footer shows Risk Score, Threat Level, and a hint to configure API keys for deeper coverage.

### Commands

`drecon` is a short alias for `deadrecon`. The old `phantomsignal` and `psig` commands still work.

| Command | What it does |
|---------|--------------|
| `init` | Create the default config and database |
| `web` | Start the web console (`--host`, `--port`, `--open-browser`, `--debug`) |
| `scan <target>` | Run a scan |
| `profile` | Build a people profile (`--email`, `--first-name`, `--last-name`, `--phone`, `--username`, `--output`) |
| `export <scan-id>` | Export a saved scan (`--format`, `--output`, `--compress`, `--encrypt`, `--password`) |
| `diff <target>` | Compare the two most recent completed scans of a target |
| `status` | Show API sources and recent scans |
| `tor on\|off\|status` | Turn Tor on or off for later scans, or show whether it's on |
| `set-password` | Create the operator account or reset its password (`--username`) |
| `api-token` | Create a REST API token, which revokes the previous one |

### Scan flags

| Flag | Description |
|------|-------------|
| `--type web_recon\|ip_recon\|domain_recon\|people_intel\|full_spectrum` | Scan type (default: `web_recon`) |
| `--profile quick\|standard\|deep\|covert` | Scan profile (default: `standard`) |
| `--modules <name>` | Modules to run. Repeat the flag or separate names with commas. Unknown names are an error. See `deadrecon scan --help` for the list |
| `--format json\|csv\|html\|xml\|xlsx\|pdf\|markdown\|stix` | Report format (default: `json`) |
| `--output <path>` | Output directory (default: `~/.deadrecon/exports`) |
| `--compress` | Compress the report into a ZIP file |
| `--encrypt`, `--password <password>` | Encrypt the report |
| `--tor` | Use Tor for this scan, and stop if it can't be confirmed |
| `--opsec off\|quiet\|paranoid` | Stealth profile for target-facing HTTP |
| `--no-robots` | Ignore robots.txt |
| `--stealth decoy\|idle`, `--decoys <spec>`, `--zombie <host>` | Decoy or idle port scan (needs nmap and root) |

---

## 9. Troubleshooting

### Linux

**Port 5000 already in use**
```bash
fuser -k 5000/tcp
python run.py
```

**`pip install` fails with missing system libs (cryptography)**
```bash
sudo apt-get install -y build-essential libssl-dev libffi-dev
pip install -e .
```

**SQLite database locked**
```bash
# Kill any stale DeadRecon process
pkill -f "python run.py"
# If the DB is still locked (it's in the folder you started DeadRecon from):
fuser deadrecon.db
```

**SocketIO connection shows "CONNECTING..." permanently**

Check that your browser isn't blocking WebSocket connections. If running behind a reverse proxy (nginx), add:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

**Permission denied on `/deadrecon/data/`**
```bash
chmod 755 deadrecon/data
```

---

### macOS

**`Python 3.10+` not found**
```bash
brew install python@3.11
# Then use python3.11 explicitly:
python3.11 -m venv .venv
```

**`cryptography` build fails on Apple Silicon (M1/M2/M3)**
```bash
brew install openssl rust
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include"
pip install cryptography
```

**Port 5000 blocked by AirPlay Receiver (macOS Monterey+)**

macOS Monterey and later reserves port 5000 for AirPlay. Either disable AirPlay Receiver in *System Settings → General → AirDrop & Handoff*, or run DeadRecon on a different port:
```bash
DEADRECON_PORT=5001 python run.py
# Then open http://127.0.0.1:5001
```

**`ssl: CERTIFICATE_VERIFY_FAILED` errors during scans**
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
# Or:
pip install certifi
```

---

### Windows

**Running DeadRecon on Windows**

DeadRecon is primarily tested on Linux and macOS. Windows support is provided via WSL2 (recommended) or native Python.

**Recommended: WSL2**
```powershell
# In PowerShell (run as Administrator)
wsl --install
# Then open WSL terminal and follow the Linux instructions above
```

**Native Python — virtual environment activation**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
python run.py
```


**`asyncio` errors on Windows (Python 3.10)**

Add to the top of `run.py` if you see `RuntimeError: Event loop is closed`:
```python
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

**Firewall blocking port 5000**

Allow inbound connections to port 5000 in Windows Defender Firewall, or use `localhost` only (default behaviour is already localhost-bound).

---

### Docker

**Container starts but web UI is unreachable**
```bash
# Check container is running
docker-compose ps

# Check logs for errors
docker-compose logs deadrecon

# Confirm port binding
docker-compose port deadrecon 5000
```

**API keys not persisting between container restarts**

Mount a volume for the data directory:
```yaml
# docker-compose.yml
volumes:
  - ./data:/app/deadrecon/data
```

**Database migration errors on upgrade**
```bash
docker-compose down
docker volume rm deadrecon_deadrecon-data
docker-compose up -d
```
> ⚠ This clears all scan history. Back up `/app/data/deadrecon.db` from the container first.

**Scans complete instantly with 0 results (DNS not resolving in container)**
```bash
# Test DNS inside container
docker-compose exec deadrecon nslookup example.com

# If failing, add DNS servers to docker-compose.yml:
services:
  deadrecon:
    dns:
      - 8.8.8.8
      - 1.1.1.1
```

**Out of memory during Deep Dive scans**

Increase Docker Desktop memory allocation (Settings → Resources → Memory) to at least 2 GB. For very large targets, 4 GB recommended.

**The Tor button shows "Tor failed"**

Hover over the button to see why. Tor usually needs under a minute to connect the first time. If your network blocks Tor, run your own Tor with bridges and set `DEADRECON_TOR_HOST`. Nothing is sent while Tor is failed.

**Rebuilding after code changes**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Getting Help

- **GitHub Issues:** https://github.com/getdeadrecon/deadrecon/issues
- **About page:** Click **ABOUT** in the footer for version info and capability overview
- **Logs:** Check the terminal running DeadRecon (manual) or `docker-compose logs` (Docker) for detailed error output
