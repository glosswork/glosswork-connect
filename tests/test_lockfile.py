"""The lockfile names only the public package index.

`uv lock` writes the index each package was resolved from into `uv.lock`. A developer's own
uv configuration can name a private index, and a plain `uv lock` then records that index's
URL in this file even though the packages themselves come from PyPI. In a repository that
people clone, that URL is a disclosure about whoever owns the index. So the kit is locked
with `UV_NO_CONFIG=1`, and this test fails when a lock slips through without it.

The second test is an allowlist of hosts rather than a check for one known URL, so a
different private index, a direct URL source or a git source fails too.
"""

import re
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCKFILE = REPO_ROOT / "uv.lock"

PUBLIC_INDEX = "https://pypi.org/simple"
ALLOWED_HOSTS = {"pypi.org", "files.pythonhosted.org"}

URL = re.compile(r"https?://[^\s\"'<>]+")


def test_every_registry_source_is_the_public_index() -> None:
    lock = tomllib.loads(LOCKFILE.read_text(encoding="utf-8"))
    registries = [
        package["source"]["registry"]
        for package in lock.get("package", [])
        if "registry" in package.get("source", {})
    ]
    assert registries, "uv.lock names no registry source, so this test reads nothing"
    others = sorted(set(registries) - {PUBLIC_INDEX})
    assert not others, f"uv.lock names a registry other than {PUBLIC_INDEX}: {others}"


def test_every_url_in_the_lockfile_is_on_an_allowed_host() -> None:
    urls = URL.findall(LOCKFILE.read_text(encoding="utf-8"))
    assert urls, "uv.lock holds no URL, so this test reads nothing"
    hosts = sorted({urlsplit(url).hostname or url for url in urls} - ALLOWED_HOSTS)
    assert not hosts, f"uv.lock names a host outside {sorted(ALLOWED_HOSTS)}: {hosts}"
