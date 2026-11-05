"""
DeadRecon Web Interface — Control Panel
Flask + SocketIO powered OSINT dashboard.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime
from functools import wraps
from typing import Optional
from urllib.parse import urlsplit

from flask import Flask
from flask_login import current_user
from flask_socketio import SocketIO, emit, join_room, leave_room

from deadrecon import __version__, __codename__
from deadrecon.core.config import config as deadrecon_config
from deadrecon.core import tor_service
from deadrecon.core.database import init_db
from deadrecon.web.auth import csp_nonce

logger = logging.getLogger("deadrecon.web")

MAX_REQUEST_BYTES = 16 * 1024 * 1024

socketio = SocketIO(async_mode="threading", logger=False)


def safe_url(value) -> str:
    """Template filter for links built from scan data: only http(s) URLs pass, so
    a hostile source can't plant a javascript: link."""
    try:
        parts = urlsplit(str(value).strip())
    except ValueError:
        return "#"
    return str(value).strip() if parts.scheme.lower() in ("http", "https") and parts.netloc else "#"


def _allowed_origins():
    """Extra Socket.IO origins (e.g. a reverse proxy's public URL). None means
    same-origin only."""
    origins = deadrecon_config.get("server", "allowed_origins", default=None)
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    return origins or None


def _socket_auth_required(handler):
    """Re-check per event: a socket outlives the login it connected with."""
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return None
        return handler(*args, **kwargs)
    return wrapper


def create_app(config_path: Optional[str] = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = deadrecon_config.get_or_create_secret_key()
    app.config["SQLALCHEMY_DATABASE_URI"] = deadrecon_config.get("database", "url", default="sqlite:///deadrecon.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DEADRECON_VERSION"] = __version__
    app.config["DEADRECON_CODENAME"] = __codename__
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES
    app.add_template_filter(safe_url, "safe_url")

    init_db()
    tor_service.resume(deadrecon_config)

    from deadrecon.core.engine import engine as recon_engine
    recon_engine._socketio = socketio
    app.recon_engine = recon_engine

    socketio.init_app(app, cors_allowed_origins=_allowed_origins())

    from deadrecon.web.auth import init_auth
    init_auth(app)

    from deadrecon.web.routes.dashboard import dashboard_bp
    from deadrecon.web.routes.scans import scans_bp
    from deadrecon.web.routes.intel import intel_bp
    from deadrecon.web.routes.settings import settings_bp
    from deadrecon.web.routes.export import export_bp
    from deadrecon.web.routes.api import api_bp
    from deadrecon.web.routes.identity import identity_bp
    from deadrecon.web.routes.locate import locate_bp
    from deadrecon.web.routes.geo import geo_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scans_bp, url_prefix="/scans")
    app.register_blueprint(intel_bp, url_prefix="/intel")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(export_bp, url_prefix="/export")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(identity_bp, url_prefix="/identity")
    app.register_blueprint(locate_bp, url_prefix="/locate")
    app.register_blueprint(geo_bp, url_prefix="/geo")

    @app.context_processor
    def inject_globals():
        from deadrecon.core.http import stealth_status
        from deadrecon.core.config import config
        try:
            stealth = stealth_status(config)
        except Exception:
            stealth = {"level": "off", "label": "DIRECT"}
        return {
            "now": datetime.utcnow(),
            "version": __version__,
            "codename": __codename__,
            "stealth": stealth,
            "csp_nonce": csp_nonce,
        }

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    _register_socketio_handlers(app)

    return app


def _register_socketio_handlers(app: Flask) -> None:
    @socketio.on("connect")
    def on_connect():
        if not current_user.is_authenticated:
            return False  # refuses the connection
        emit("server_ready", {
            "message": "Connected. Ready to scan.",
            "version": __version__,
            "codename": __codename__,
        })

    @socketio.on("disconnect")
    def on_disconnect():
        logger.debug("Client disconnected from the grid")

    @socketio.on("join_scan")
    @_socket_auth_required
    def on_join_scan(data):
        scan_id = data.get("scan_id")
        if scan_id:
            join_room(f"scan_{scan_id}")
            emit("joined_scan", {"scan_id": scan_id, "message": f"Connected to scan {scan_id[:8]}..."})
            # Send current progress so late-joining browsers can sync immediately.
            with app.app_context():
                from deadrecon.core.database import get_db
                from deadrecon.core.models import Scan
                try:
                    with get_db() as db:
                        scan = db.query(Scan).filter(Scan.id == scan_id).first()
                        if scan and scan.status.value == "running":
                            emit("scan_status", {
                                "scan_id": scan_id,
                                "progress": scan.progress or 0,
                                "status": scan.status.value,
                            })
                except Exception:
                    pass

    @socketio.on("leave_scan")
    @_socket_auth_required
    def on_leave_scan(data):
        scan_id = data.get("scan_id")
        if scan_id:
            leave_room(f"scan_{scan_id}")

    @socketio.on("abort_scan")
    @_socket_auth_required
    def on_abort_scan(data):
        scan_id = data.get("scan_id")
        if scan_id:
            app.recon_engine.abort_scan(scan_id)
            emit("scan_aborted", {"scan_id": scan_id})

    @socketio.on("ping")
    @_socket_auth_required
    def on_ping():
        emit("pong", {"timestamp": datetime.utcnow().isoformat()})


def run_scan_async(app: Flask, scan_id: str) -> None:
    """Launch a scan in a background thread with its own asyncio loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with app.app_context():
            loop.run_until_complete(app.recon_engine.launch_scan(scan_id))
        loop.close()

    thread = threading.Thread(target=_run, daemon=True, name=f"scan-{scan_id[:8]}")
    thread.start()
