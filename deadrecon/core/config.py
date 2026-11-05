"""
DeadRecon Configuration Manager — Ghost Keys & Grid Settings

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from deadrecon.core.legacy import alias_legacy_env, migrate_home, migrate_sqlite_db

load_dotenv()
alias_legacy_env()

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "deadrecon.yaml"
_USER_CONFIG_PATH = Path.home() / ".deadrecon" / "config.yaml"


def default_export_dir() -> Path:
    return _USER_CONFIG_PATH.parent / "exports"


def _write_private(path: Path, text: str) -> None:
    """Atomically write an owner-only file. These hold API keys, proxy credentials
    and the session signing key, so they must not be readable by other users."""
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")  # created 0600
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class DeadReconConfig:
    """Central configuration hub for the DeadRecon grid."""

    _instance: Optional["DeadReconConfig"] = None

    def __new__(cls, config_path: Optional[str] = None) -> "DeadReconConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._config: Dict[str, Any] = {}
        migrate_home(_USER_CONFIG_PATH.parent)
        self._load_defaults()
        legacy_default = _DEFAULT_CONFIG_PATH.with_name("phantomsignal.yaml")
        self._load_file(_DEFAULT_CONFIG_PATH if _DEFAULT_CONFIG_PATH.exists() or not legacy_default.exists()
                        else legacy_default)
        if _USER_CONFIG_PATH.exists():
            self._load_file(_USER_CONFIG_PATH)
        if config_path:
            self._load_file(Path(config_path))
        self._apply_env_overrides()
        migrate_sqlite_db(self.get("database", "url", default="sqlite:///deadrecon.db"))

    def _load_defaults(self) -> None:
        self._config = {
            "server": {
                "host": "127.0.0.1",
                "port": 5000,
                "debug": False,
                "secret_key": None,  # see get_or_create_secret_key()
                "secure_cookies": False,
                "allowed_origins": [],
                "workers": 4,
            },
            "database": {
                "url": "sqlite:///deadrecon.db",
                "pool_size": 10,
                "echo": False,
            },
            "scraper": {
                "concurrent_requests": 16,
                "download_delay": 1.0,
                "randomize_delay": True,
                "respect_robots_txt": True,
                "user_agent_rotation": True,
                "follow_redirects": True,
                "max_depth": 3,
                "timeout": 30,
                "javascript_rendering": False,
                "proxy": None,
                "tor_enabled": False,
                "tor_host": "127.0.0.1",
                "tor_port": 9050,
                "tor_verify": True,
                # Stealth posture for target-facing HTTP: off | quiet | paranoid.
                # Consumed by core.http; "off" preserves legacy fast behaviour.
                "stealth_profile": "off",
                # Rotating egress pool (list of http/https/socks5 URLs). Empty =
                # use single `proxy` above, or direct. proxy_rotation:
                # sticky (per-host, rotate on burn) | every (per-request).
                "proxy_pool": [],
                "proxy_rotation": "sticky",
                # Present a real browser TLS (JA3/JA4) + HTTP/2 fingerprint via
                # curl_cffi, matched to the per-host browser identity. Needs the
                # optional `curl_cffi` package; degrades to standard TLS without.
                "tls_impersonate": False,
            },
            "port_scanner": {
                "default_ports": [
                    21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
                    993, 995, 1433, 1521, 3306, 3389, 5432, 5900,
                    6379, 8080, 8443, 8888, 9200, 27017,
                ],
                "max_concurrent": 500,
                "timeout": 3,
                "service_detection": True,
            },
            "intel": {
                "enabled_apis": [],
                "rate_limit_buffer": 0.5,
                "cache_ttl": 3600,
                "auto_correlate": True,
                "shadow_scoring": True,
            },
            "export": {
                "default_format": "json",
                "output_dir": None,  # default_export_dir()
                "compression": False,
                "encryption": False,
                "encryption_algorithm": "AES-256-GCM",
            },
            "evasive": {
                "enabled": False,
                "rotate_identity": True,
                "header_spoofing": True,
                "delay_jitter": True,
                "jitter_range": [0.5, 3.0],
            },
            "geo": {
                # Locate map. No basemap by default: a tile provider sees which areas
                # the operator views. Set tile_url to your own or a keyed provider.
                "map_tiles": True,
                "tile_url": "",
                "tile_url_dark": "",
                "tile_attribution": "",
            },
            "neural_profiler": {
                "enabled": False,
                "model": "local",
                "confidence_threshold": 0.75,
            },
            "notifications": {
                "desktop": True,
                "webhook_url": None,
                "slack_token": None,
            },
            "api_keys": {},
        }

    def _load_file(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        self._deep_merge(self._config, data)

    def _deep_merge(self, base: dict, override: dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        env_map = {
            "DEADRECON_HOST": ("server", "host"),
            "DEADRECON_PORT": ("server", "port"),
            "DEADRECON_DEBUG": ("server", "debug"),
            "DEADRECON_DB_URL": ("database", "url"),
            "DEADRECON_SECRET_KEY": ("server", "secret_key"),
            "DEADRECON_SECURE_COOKIES": ("server", "secure_cookies"),
            "DEADRECON_ALLOWED_ORIGINS": ("server", "allowed_origins"),
            "DEADRECON_TOR_ENABLED": ("scraper", "tor_enabled"),
            "DEADRECON_TOR_HOST": ("scraper", "tor_host"),
            "DEADRECON_TOR_PORT": ("scraper", "tor_port"),
            "DEADRECON_PROXY": ("scraper", "proxy"),
            "DEADRECON_EXPORT_DIR": ("export", "output_dir"),
        }
        api_key_envs = {
            "SHODAN_API_KEY": "shodan",
            "CENSYS_API_ID": "censys_id",
            "CENSYS_API_SECRET": "censys_secret",
            "HUNTER_API_KEY": "hunter",
            "HIBP_API_KEY": "hibp",
            "VIRUSTOTAL_API_KEY": "virustotal",
            "ABUSEIPDB_API_KEY": "abuseipdb",
            "GREYNOISE_API_KEY": "greynoise",
            "IPINFO_TOKEN": "ipinfo",
            "SECURITYTRAILS_API_KEY": "securitytrails",
            "URLSCAN_API_KEY": "urlscan",
            "ALIENVAULT_API_KEY": "alienvault",
            "GITHUB_TOKEN": "github",
            "TWITTER_BEARER_TOKEN": "twitter_bearer",
            "ZOOMEYE_API_KEY": "zoomeye",
            "FULLCONTACT_API_KEY": "fullcontact",
            "PIPL_API_KEY": "pipl",
            "BINARYEDGE_API_KEY": "binaryedge",
            "SPYSE_API_KEY": "spyse",
            "RISKIQ_USERNAME": "riskiq_user",
            "RISKIQ_KEY": "riskiq_key",
            "WHOISXML_API_KEY": "whoisxml",
            "GOOGLE_CSE_KEY": "google_cse",
            "GOOGLE_CSE_ID": "google_cse_id",
            "BING_SEARCH_KEY": "bing",
            "SPOKEO_API_KEY": "spokeo",
            "WHITEPAGES_API_KEY": "whitepages",
            "INTELIUS_API_KEY": "intelius",
            "CLEARBIT_API_KEY": "clearbit",
            "TELEGRAM_BOT_TOKEN": "telegram",
            # Expanded social / people intel
            "TWITCH_CLIENT_ID": "twitch_client_id",
            "TWITCH_CLIENT_SECRET": "twitch_client_secret",
            "SPOTIFY_CLIENT_ID": "spotify_client_id",
            "SPOTIFY_CLIENT_SECRET": "spotify_client_secret",
            "STEAM_API_KEY": "steam",
            "VK_ACCESS_TOKEN": "vk",
            "TUMBLR_API_KEY": "tumblr",
            "FLICKR_API_KEY": "flickr",
            "DISCORD_BOT_TOKEN": "discord",
            "FACEBOOK_ACCESS_TOKEN": "facebook",
            "INTELX_API_KEY": "intelx",
            "ABSTRACTAPI_PHONE_KEY": "abstractapi_phone",
            "EMAILREP_API_KEY": "emailrep",
            "LINKEDIN_RAPIDAPI_KEY": "linkedin_rapidapi",
            "TIKTOK_CLIENT_KEY": "tiktok_client_key",
            "TIKTOK_CLIENT_SECRET": "tiktok_client_secret",
            "INSTAGRAM_ACCESS_TOKEN": "instagram",
            "TWITTER_API_KEY": "twitter",
        }
        for env_var, (section, key) in env_map.items():
            val = os.getenv(env_var)
            if val is not None:
                if key in ("port",):
                    val = int(val)
                elif val.lower() in ("true", "false"):
                    val = val.lower() == "true"
                self._config[section][key] = val

        for env_var, api_name in api_key_envs.items():
            val = os.getenv(env_var)
            if val:
                self._config["api_keys"][api_name] = val

    def get(self, *keys: str, default: Any = None) -> Any:
        node = self._config
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k, default)
        return node

    def set(self, *keys: str, value: Any) -> None:
        node = self._config
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value

    def get_api_key(self, service: str) -> Optional[str]:
        return self._config["api_keys"].get(service)

    def set_api_key(self, service: str, key: str) -> None:
        self._config["api_keys"][service] = key
        self._persist_user_config(include_api_keys=True)

    # Scraper/egress fields that survive a restart — the ones the Scan Settings
    # UI edits. Kept explicit (not the whole scraper block) so volatile or
    # env-driven defaults aren't frozen into the user config file.
    _PERSIST_SCRAPER_KEYS = (
        "stealth_profile", "proxy", "proxy_pool", "proxy_rotation",
        "tls_impersonate", "tor_enabled", "respect_robots_txt",
        "download_delay", "concurrent_requests",
    )

    def refresh_tor_setting(self) -> None:
        """Picks up ``deadrecon tor on`` from another process, such as the Docker
        covert profile. An environment variable still wins."""
        if os.getenv("DEADRECON_TOR_ENABLED") or not _USER_CONFIG_PATH.exists():
            return
        try:
            with open(_USER_CONFIG_PATH) as f:
                saved = (yaml.safe_load(f) or {}).get("scraper") or {}
        except Exception:
            return
        if "tor_enabled" in saved:
            self.set("scraper", "tor_enabled", value=bool(saved["tor_enabled"]))

    def persist(self) -> None:
        """Persist the scraper/egress settings to the user config file so they
        survive a restart. API keys already on disk are preserved untouched —
        we don't push env-provided keys into the file as a side effect."""
        self._persist_user_config(include_api_keys=False)

    def _persist_user_config(self, include_api_keys: bool = True) -> None:
        _USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Merge into whatever is already on disk so manual additions, and any
        # keys we don't manage, are preserved rather than clobbered.
        existing: Dict[str, Any] = {}
        if _USER_CONFIG_PATH.exists():
            try:
                with open(_USER_CONFIG_PATH) as f:
                    existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

        # Only rewrite api_keys when explicitly saving one (set_api_key). The
        # scraper-settings path leaves on-disk keys as-is so env-loaded secrets
        # aren't silently copied into the config file.
        if include_api_keys:
            existing["api_keys"] = self._config.get("api_keys", {})

        scraper = self._config.get("scraper", {})
        saved_scraper = existing.get("scraper") or {}
        for k in self._PERSIST_SCRAPER_KEYS:
            if k in scraper:
                saved_scraper[k] = scraper[k]
        existing["scraper"] = saved_scraper

        _write_private(_USER_CONFIG_PATH,
                       yaml.dump(existing, default_flow_style=False, sort_keys=False))

    def get_or_create_secret_key(self) -> str:
        """The session signing key: configured, or generated once and kept in an
        owner-only file so logins survive a restart."""
        configured = self.get("server", "secret_key")
        if configured:
            return configured
        path = _USER_CONFIG_PATH.parent / "secret_key"
        if path.exists():
            return path.read_text().strip()
        key = secrets.token_hex(32)
        _write_private(path, key + "\n")
        return key

    def as_dict(self) -> Dict[str, Any]:
        import copy
        d = copy.deepcopy(self._config)
        for k in d.get("api_keys", {}):
            if d["api_keys"][k]:
                d["api_keys"][k] = "***REDACTED***"
        if d.get("server", {}).get("secret_key"):
            d["server"]["secret_key"] = "***REDACTED***"
        return d

    @property
    def server(self) -> Dict:
        return self._config["server"]

    @property
    def scraper(self) -> Dict:
        return self._config["scraper"]

    @property
    def intel(self) -> Dict:
        return self._config["intel"]

    @property
    def export(self) -> Dict:
        return self._config["export"]

    @property
    def evasive(self) -> Dict:
        return self._config["evasive"]


config = DeadReconConfig()
