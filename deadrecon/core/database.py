"""
DeadRecon Database — Persistent Signal Storage

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from deadrecon.core.config import config
from deadrecon.core.models import Base

logger = logging.getLogger("deadrecon.database")

_engine = None
_SessionFactory = None


def _restrict_sqlite_files(db_url: str) -> None:
    """Keep a SQLite database owner-only: it holds scan results, Locate cases and
    the operator's password hash. SQLite gives new -wal/-shm files the database
    file's mode, so creating it 0600 up front covers them too; files left by an
    older version are tightened here."""
    url = make_url(db_url)
    if not url.drivername.startswith("sqlite"):
        return
    database = url.database
    if not database or database == ":memory:" or database.startswith("file:"):
        return
    path = Path(database)
    try:
        os.close(os.open(path, os.O_CREAT | os.O_RDWR, 0o600))
        for suffix in ("", "-wal", "-shm", "-journal"):
            candidate = path.with_name(path.name + suffix)
            if candidate.exists():
                os.chmod(candidate, 0o600)
    except OSError as exc:
        logger.warning("Could not restrict database file permissions on %s: %s", path, exc)


def get_engine():
    global _engine
    if _engine is None:
        db_url = config.get("database", "url", default="sqlite:///deadrecon.db")
        kwargs = {}
        if db_url.startswith("sqlite"):
            kwargs["check_same_thread"] = False
            _restrict_sqlite_files(db_url)
        _engine = create_engine(
            db_url,
            echo=config.get("database", "echo", default=False),
            pool_size=config.get("database", "pool_size", default=5)
            if not db_url.startswith("sqlite")
            else None or 5,
            connect_args=kwargs if db_url.startswith("sqlite") else {},
        )
        if db_url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, _):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


def init_db() -> None:
    """Initialize the shadow network database — create all tables."""
    Base.metadata.create_all(bind=get_engine())


def drop_db() -> None:
    """Wipe the database — destroys all data. Non-reversible."""
    Base.metadata.drop_all(bind=get_engine())


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """Get a raw session — caller is responsible for commit/close."""
    return get_session_factory()()
