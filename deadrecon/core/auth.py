"""
DeadRecon operator credentials — the single account that owns a console.

Framework-free so the web layer and the CLI share one implementation. Passwords
are stored as salted scrypt hashes; API tokens are random and stored only as a
SHA-256 digest, so neither can be recovered from the database.

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from deadrecon.core.database import get_db
from deadrecon.core.models import Operator

MIN_PASSWORD_LENGTH = 12

# Verified when the username is unknown, so a miss costs the same as a wrong
# password and login timing doesn't reveal which usernames exist.
_DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


class OperatorError(ValueError):
    """A credential change was refused; the message is safe to show the user."""


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _check_password_strength(password: str) -> None:
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise OperatorError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


def has_operator() -> bool:
    with get_db() as db:
        return db.query(Operator.id).first() is not None


def get_operator() -> Optional[Operator]:
    with get_db() as db:
        return db.query(Operator).first()


def get_operator_by_id(operator_id: str) -> Optional[Operator]:
    with get_db() as db:
        return db.query(Operator).filter(Operator.id == operator_id).first()


def create_operator(username: str, password: str) -> Operator:
    """Create the console's one operator. Refused if one already exists."""
    username = (username or "").strip()
    if not username:
        raise OperatorError("Username is required.")
    _check_password_strength(password)
    with get_db() as db:
        if db.query(Operator.id).first() is not None:
            raise OperatorError("An operator account already exists.")
        operator = Operator(username=username, password_hash=generate_password_hash(password))
        db.add(operator)
        db.flush()
        return operator


def set_password(password: str) -> None:
    """Replace the operator's password. Existing sessions stop being valid."""
    _check_password_strength(password)
    with get_db() as db:
        operator = db.query(Operator).first()
        if operator is None:
            raise OperatorError("No operator account exists yet.")
        operator.password_hash = generate_password_hash(password)


def verify_credentials(username: str, password: str) -> Optional[Operator]:
    with get_db() as db:
        operator = db.query(Operator).filter(Operator.username == (username or "").strip()).first()
    stored = operator.password_hash if operator else _DUMMY_HASH
    if check_password_hash(stored, password or "") and operator:
        return operator
    return None


def session_fingerprint(operator: Operator) -> str:
    """Short digest of the password hash, embedded in the session's user id so a
    password change invalidates every session issued before it."""
    return hashlib.sha256(operator.password_hash.encode()).hexdigest()[:16]


def rotate_api_token() -> str:
    """Issue a new API token, revoking the old one. Returned once, never stored."""
    token = f"psig_{secrets.token_urlsafe(32)}"
    with get_db() as db:
        operator = db.query(Operator).first()
        if operator is None:
            raise OperatorError("No operator account exists yet.")
        operator.api_token_hash = _token_digest(token)
    return token


def verify_api_token(token: str) -> bool:
    if not token:
        return False
    with get_db() as db:
        return db.query(Operator.id).filter(
            Operator.api_token_hash == _token_digest(token)).first() is not None
