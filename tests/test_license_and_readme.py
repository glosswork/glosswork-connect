"""The license, and the README's promise to name every piece.

The kit is MIT while the server is not. That difference is deliberate and easy to undo by
copying the wrong file in, so it is asserted rather than remembered.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Each piece, as README.md has to name it, so that the table cannot quietly lose a row.
PIECE_PATHS = (
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    "skills/",
    "mcpb/",
    "connect/",
    "wrappers/",
)


def test_the_license_is_mit() -> None:
    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License")
    assert "Heavylift Labs LLC" in license_text


def test_the_license_is_not_the_product_repository_s() -> None:
    """The server's license is a different one. Copying it in here would quietly close the
    two directories the kit is MIT in order to satisfy."""
    for name in ("LICENSE", "README.md", ".claude-plugin/plugin.json"):
        assert "FSL-1.1" not in (REPO_ROOT / name).read_text(encoding="utf-8"), name


def test_the_plugin_manifest_agrees_with_the_license_file() -> None:
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))
    assert manifest["license"] == "MIT"


@pytest.mark.parametrize("piece", PIECE_PATHS)
def test_the_readme_names_every_piece(piece: str) -> None:
    assert piece in (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def test_the_readme_names_the_github_home_and_not_gitlab() -> None:
    """The source of truth is on GitHub. The history before the move is kept in a private
    archive, which the README does not link, because this file is public."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/glosswork/glosswork-connect" in readme
    assert "gitlab.com" not in readme


# Text that was true while the repository was private, or before the extension was
# installed in Claude Desktop. Each is matched after whitespace is collapsed, so a phrase
# broken across lines cannot slip past.
STALE_README_PHRASES = (
    "<path to a clone",
    "second header",
    "private until",
    "a file sent",
    "not yet installed in Claude Desktop",
    "installed in Claude Desktop yet",
)


def test_the_readme_installs_from_github_and_says_nothing_stale() -> None:
    """The marketplace is added from GitHub, which copies only the repository's files. A
    local directory is copied whole, untracked files included, so the README must not send
    a reader there by default."""
    readme = " ".join((REPO_ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "claude plugin marketplace add glosswork/glosswork-connect" in readme
    present = [phrase for phrase in STALE_README_PHRASES if phrase in readme]
    assert not present, f"README.md still says: {present}"
