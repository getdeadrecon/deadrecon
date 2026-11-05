"""
DeadRecon console access control.

One ``before_request`` guard protects every endpoint, so a new route is private
unless it is added to ``PUBLIC_ENDPOINTS``. Browser sessions must pass CSRF checks
on unsafe methods; the REST API also accepts a bearer token, which browsers never
send on their own and so needs no CSRF token.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import hmac
import secrets
import sys
import threading
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

from flask import (
    g,
    Blueprint, Flask, current_app, flash, jsonify, redirect, render_template,
    request, session, url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_wtf.csrf import CSRFError, CSRFProtect

from deadrecon.core import auth as operators
from deadrecon.core.config import config

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
csrf = CSRFProtect()

PUBLIC_ENDPOINTS = {"auth.login", "auth.setup", "api.health", "static"}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

MAX_FAILED_ATTEMPTS = 5
FAILED_ATTEMPT_WINDOW = 300  # seconds


class _FailedAttempts:
    """In-memory per-client throttle for password and setup-token guesses."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._attempts: Dict[str, List[float]] = {}

    def _recent(self, key: str, now: float) -> List[float]:
        return [t for t in self._attempts.get(key, []) if now - t < FAILED_ATTEMPT_WINDOW]

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key, time.monotonic())) >= MAX_FAILED_ATTEMPTS

    def record(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._attempts = {k: r for k in self._attempts if (r := self._recent(k, now))}
            self._attempts[key] = self._recent(key, now) + [now]

    def clear(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


_failed = _FailedAttempts()


class SessionUser(UserMixin):
    def __init__(self, operator) -> None:
        self.username = operator.username
        self.id = f"{operator.id}:{operators.session_fingerprint(operator)}"


@login_manager.user_loader
def _load_user(session_id: str) -> Optional[SessionUser]:
    operator_id, _, fingerprint = session_id.partition(":")
    operator = operators.get_operator_by_id(operator_id)
    if operator is None:
        return None
    if not hmac.compare_digest(fingerprint, operators.session_fingerprint(operator)):
        return None
    return SessionUser(operator)


def _is_api_request() -> bool:
    return request.blueprint == "api" or request.endpoint == "export.api_export"


def _bearer_token() -> Optional[str]:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    return token.strip() if scheme.lower() == "bearer" else None


def _unauthorized():
    if _is_api_request():
        response = jsonify({"status": "error", "message": "Authentication required"})
        response.headers["WWW-Authenticate"] = "Bearer"
        return response, 401
    next_path = request.full_path.rstrip("?") if request.method == "GET" else None
    return redirect(url_for("auth.login", next=next_path))


def _guard():
    if request.endpoint in PUBLIC_ENDPOINTS:
        if request.method not in SAFE_METHODS:
            csrf.protect()
        return None

    if _is_api_request():
        token = _bearer_token()
        if token is not None:
            return None if operators.verify_api_token(token) else _unauthorized()

    if not current_user.is_authenticated:
        return _unauthorized()
    if request.method not in SAFE_METHODS:
        csrf.protect()
    return None


def _safe_next(target: Optional[str]) -> str:
    """Only follow same-site paths, so a crafted login link can't redirect away."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        parsed = urlparse(target)
        if not parsed.scheme and not parsed.netloc:
            return target
    return url_for("dashboard.index")


def _begin_session(operator) -> None:
    session.clear()
    login_user(SessionUser(operator))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not operators.has_operator():
        return redirect(url_for("auth.setup"))
    if current_user.is_authenticated:
        return redirect(_safe_next(request.args.get("next")))

    if request.method != "POST":
        return render_template("auth/login.html", next_path=request.args.get("next", ""))

    next_path = request.form.get("next", "")
    client = request.remote_addr or "unknown"
    if _failed.blocked(client):
        flash("Too many failed attempts. Try again in a few minutes.", "error")
        return render_template("auth/login.html", next_path=next_path), 429

    operator = operators.verify_credentials(
        request.form.get("username", ""), request.form.get("password", ""))
    if operator is None:
        _failed.record(client)
        flash("Incorrect username or password.", "error")
        return render_template("auth/login.html", next_path=next_path), 401

    _failed.clear(client)
    _begin_session(operator)
    return redirect(_safe_next(next_path))


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """First-run account creation, gated by a token printed to the server log so
    whoever first reaches an exposed port can't claim the console."""
    if operators.has_operator():
        return redirect(url_for("auth.login"))

    if request.method != "POST":
        return render_template("auth/setup.html", min_length=operators.MIN_PASSWORD_LENGTH)

    def refuse(message: str, status: int):
        flash(message, "error")
        return render_template("auth/setup.html", min_length=operators.MIN_PASSWORD_LENGTH), status

    client = request.remote_addr or "unknown"
    if _failed.blocked(client):
        return refuse("Too many failed attempts. Try again in a few minutes.", 429)

    expected = current_app.config.get("DEADRECON_SETUP_TOKEN") or ""
    supplied = request.form.get("setup_token", "").strip()
    if not expected or not hmac.compare_digest(supplied.encode(), expected.encode()):
        _failed.record(client)
        return refuse("Incorrect setup token. Check the server's startup output.", 403)

    password = request.form.get("password", "")
    if password != request.form.get("confirm_password", ""):
        return refuse("Passwords don't match.", 400)
    try:
        operator = operators.create_operator(request.form.get("username", ""), password)
    except operators.OperatorError as exc:
        return refuse(str(exc), 400)

    _failed.clear(client)
    current_app.config.pop("DEADRECON_SETUP_TOKEN", None)
    _begin_session(operator)
    flash("Operator account created.", "success")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))


def _announce_setup_token(token: str) -> None:
    print(
        "\n>> First run: no operator account exists yet.\n"
        f"   Open the console and enter this setup token: {token}\n"
        "   (Or run `deadrecon set-password` to create the account from the CLI.)\n",
        file=sys.stderr, flush=True,
    )


def _tile_sources() -> List[str]:
    """Map-tile hosts for img-src. A {s} subdomain placeholder becomes a wildcard."""
    sources = []
    for key in ("tile_url", "tile_url_dark"):
        url = config.get("geo", key, default=None)
        if url:
            parts = urlparse(str(url).replace("{s}", "*"))
            if parts.scheme in ("http", "https") and parts.netloc:
                sources.append(f"{parts.scheme}://{parts.netloc}")
    return list(dict.fromkeys(sources))


def csp_nonce() -> str:
    """This response's script nonce. Only tagged inline scripts run, so markup injected
    from scan data can't execute. Inline styles are still allowed."""
    if "csp_nonce" not in g:
        g.csp_nonce = secrets.token_urlsafe(16)
    return g.csp_nonce


def _content_security_policy() -> str:
    """Limits where the console can load from and send data to."""
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'nonce-{csp_nonce()}' https://cdnjs.cloudflare.com https://unpkg.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com",
        "font-src 'self' https://fonts.gstatic.com",
        " ".join(["img-src 'self' data: https://unpkg.com", *_tile_sources()]),
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
    ])


def _configured_flag(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def init_auth(app: Flask) -> None:
    app.config.update(
        SESSION_COOKIE_NAME="deadrecon_session",  # cookies ignore ports; don't clash locally
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_configured_flag(
            config.get("server", "secure_cookies", default=False)),
        WTF_CSRF_CHECK_DEFAULT=False,  # _guard decides when to check
        WTF_CSRF_TIME_LIMIT=None,      # tokens live as long as the session
    )
    csrf.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.before_request(_guard)

    @app.errorhandler(CSRFError)
    def on_csrf_error(error):
        if _is_api_request():
            return jsonify({"status": "error", "message": error.description}), 400
        flash("Your session expired or the form was out of date. Please try again.", "warning")
        return redirect(url_for("auth.login"))

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy", _content_security_policy())
        return response

    if not operators.has_operator():
        token = secrets.token_urlsafe(16)
        app.config["DEADRECON_SETUP_TOKEN"] = token
        _announce_setup_token(token)
