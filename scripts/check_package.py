#!/usr/bin/env python3
"""Check built packages before they ship.

Fails if a wheel or sdist is missing data files the code needs at runtime, or
contains anything private (tests, local config, databases, keys).

Usage: python scripts/check_package.py dist/*.whl dist/*.tar.gz
"""
import re
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORED_DATA = {".gitkeep"}
FORBIDDEN = re.compile(
    r"(^|/)(tests|config)/"
    r"|\.(db|db-wal|db-shm|sqlite3?|pem|key|p12|pfx|enc|kml|geojson)$"
    r"|(^|/)(\.env(\..*)?|secret_key|\.pypirc|\.netrc)$"
)


def required_data_files():
    """Every non-Python file in the package source tree."""
    for path in (ROOT / "deadrecon").rglob("*"):
        if (path.is_file() and path.suffix not in (".py", ".pyc")
                and path.name not in IGNORED_DATA and "__pycache__" not in path.parts):
            yield path.relative_to(ROOT).as_posix()


def package_names(path):
    """File names in a package, relative to the package root."""
    if path.endswith(".whl"):
        with zipfile.ZipFile(path) as wheel:
            return set(wheel.namelist())
    with tarfile.open(path) as sdist:
        return {name.split("/", 1)[1] for name in sdist.getnames() if "/" in name}


def check(path):
    names = package_names(path)
    errors = [f"missing {name}" for name in required_data_files() if name not in names]
    errors += [f"must not ship {name}" for name in sorted(names) if FORBIDDEN.search(name)]
    return errors


def main(paths):
    if not paths:
        print(__doc__)
        return 2
    failed = False
    for path in paths:
        errors = check(path)
        print(f"{Path(path).name}: {'OK' if not errors else 'FAILED'}")
        for error in errors:
            print(f"  {error}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
