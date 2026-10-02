"""The kit's shape: the directories and files every other change builds on."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# One directory per piece named in README.md. A piece that is not built yet still owns
# its directory, so that a plan can put work in an obvious place.
PIECE_DIRECTORIES = ("skills", "mcpb", "connect", "wrappers")

ROOT_DOCUMENTS = ("README.md", "AGENTS.md", "CONTRIBUTING.md", "LICENSE")


@pytest.mark.parametrize("name", PIECE_DIRECTORIES)
def test_each_piece_has_a_directory(name: str) -> None:
    assert (REPO_ROOT / name).is_dir(), f"{name}/ is missing"


@pytest.mark.parametrize("name", PIECE_DIRECTORIES)
def test_each_piece_directory_explains_itself(name: str) -> None:
    """A directory holding nothing but a README is fine. An empty one is not: it tells a
    reader nothing about what belongs there or what has to be true before it is built."""
    contents = [path for path in (REPO_ROOT / name).iterdir() if path.name != ".DS_Store"]
    assert contents, f"{name}/ is empty"


@pytest.mark.parametrize("name", ROOT_DOCUMENTS)
def test_root_documents_exist(name: str) -> None:
    assert (REPO_ROOT / name).is_file(), f"{name} is missing"


def test_the_marketplace_file_is_at_the_root() -> None:
    """Claude Code looks for the marketplace at exactly this path in a repository root."""
    assert (REPO_ROOT / ".claude-plugin" / "marketplace.json").is_file()


def test_the_repository_root_is_the_plugin() -> None:
    """Plugin manifest paths cannot escape the plugin directory, so the plugin root is the
    repository root. That is what lets the top-level skills/ folder be the plugin's own."""
    assert (REPO_ROOT / ".claude-plugin" / "plugin.json").is_file()
    assert (REPO_ROOT / ".mcp.json").is_file()


def test_the_change_plan_directory_holds_only_its_readme() -> None:
    """A plan file lives on its own branch and is deleted at merge. On main, only the
    README is ever there; anything else is a plan that outlived its change."""
    residents = sorted(p.name for p in (REPO_ROOT / "docs" / "changes").iterdir())
    assert residents == ["README.md"]


def test_every_skill_declares_a_name_and_a_description() -> None:
    """A skill with no description never loads: the description is what tells a harness
    when to reach for it."""
    skill_files = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    assert skill_files, "skills/ holds no SKILL.md"
    for skill_file in skill_files:
        text = skill_file.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{skill_file.name} has no front matter"
        front_matter = text.split("---", 2)[1]
        assert "name:" in front_matter, f"{skill_file} declares no name"
        assert "description:" in front_matter, f"{skill_file} declares no description"


def test_the_clone_does_not_offer_the_plugins_server_as_a_project_server() -> None:
    """The repository root is the plugin root, so a Claude Code session started in a clone
    would also read `.mcp.json` as a project server, with a literal
    `${user_config.address}`. The project setting turns exactly those servers off."""
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text("utf-8"))
    servers = json.loads((REPO_ROOT / ".mcp.json").read_text("utf-8"))["mcpServers"]
    assert settings["disabledMcpjsonServers"] == list(servers)
