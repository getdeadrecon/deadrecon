"""
Keeps installs from before the rename to DeadRecon (1.30.0) working.

Older versions were called PhantomSignal. Their environment variables still work,
and their config folder and default database move to the new names on first run.
"""

import logging
import os
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

logger = logging.getLogger("deadrecon.core.legacy")

_OLD_ENV_PREFIX = "PHANTOMSIGNAL_"
_NEW_ENV_PREFIX = "DEADRECON_"
_OLD_HOME_NAME = ".phantomsignal"
_NEW_DB_NAME = "deadrecon.db"
_OLD_DB_NAME = "phantomsignal.db"


def alias_legacy_env() -> None:
    """Make each PHANTOMSIGNAL_* variable available as DEADRECON_*. A variable
    already set under the new name wins."""
    for name, value in list(os.environ.items()):
        if name.startswith(_OLD_ENV_PREFIX):
            os.environ.setdefault(_NEW_ENV_PREFIX + name[len(_OLD_ENV_PREFIX):], value)


def migrate_home(new_dir: Path) -> None:
    """Move the old config folder to ``new_dir``. It holds API keys, the session key
    and Tor state. A link stays at the old path, because saved records can name files
    under it."""
    old_dir = new_dir.parent / _OLD_HOME_NAME
    if os.path.lexists(new_dir) or old_dir.is_symlink() or not old_dir.is_dir():
        return
    try:
        os.rename(old_dir, new_dir)
    except OSError as exc:
        logger.warning("Could not move %s to %s: %s. Move it by hand to keep your settings.",
                       old_dir, new_dir, exc)
        return
    try:
        old_dir.symlink_to(new_dir, target_is_directory=True)
    except OSError as exc:
        logger.info("Moved %s but could not link the old path: %s", old_dir, exc)


def migrate_sqlite_db(db_url: str) -> None:
    """Move an old default database next to the new one's path. The main file moves
    last, so an interrupted move is finished on the next start."""
    try:
        url = make_url(db_url)
    except ArgumentError:
        return
    if not url.drivername.startswith("sqlite") or not url.database:
        return
    new_path = Path(url.database)
    old_path = new_path.with_name(_OLD_DB_NAME)
    if new_path.name != _NEW_DB_NAME or new_path.exists() or not old_path.is_file():
        return
    try:
        for suffix in ("-wal", "-shm", "-journal", ""):
            source = old_path.with_name(old_path.name + suffix)
            if source.exists():
                os.rename(source, new_path.with_name(new_path.name + suffix))
    except OSError as exc:
        logger.warning("Could not move %s to %s: %s. Move it by hand to keep your scans.",
                       old_path, new_path, exc)
