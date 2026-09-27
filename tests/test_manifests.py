"""The manifests: what the plugin asks a person for, and where those answers go."""

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SUBSTITUTION = re.compile(r"\$\{user_config\.([A-Za-z0-9_]+)\}")


def load(relative_path: str) -> Any:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_marketplace_declares_a_name_an_owner_and_plugins() -> None:
    marketplace = load(".claude-plugin/marketplace.json")
    assert KEBAB_CASE.match(marketplace["name"])
    assert marketplace["owner"]["name"]
    assert marketplace["plugins"]


def test_every_plugin_source_is_a_relative_path() -> None:
    """The host is never named in a manifest, so a change of host is never a change to
    the manifests. A relative source resolves in a clone of any remote."""
    for plugin in load(".claude-plugin/marketplace.json")["plugins"]:
        source = plugin["source"]
        assert isinstance(source, str), f"{plugin['name']} names a host-specific source"
        assert source.startswith("./"), f"{plugin['name']} source must start with ./"
        assert (REPO_ROOT / source).is_dir(), f"{plugin['name']} source does not exist"


def test_the_plugin_manifest_carries_no_repository_url() -> None:
    plugin = load(".claude-plugin/plugin.json")
    assert "repository" not in plugin
    assert "homepage" not in plugin


def test_the_plugin_is_mit_everywhere_it_says_so() -> None:
    assert load(".claude-plugin/plugin.json")["license"] == "MIT"
    for plugin in load(".claude-plugin/marketplace.json")["plugins"]:
        assert plugin.get("license") == "MIT"


def test_the_plugin_asks_for_the_address_and_the_token_and_nothing_else() -> None:
    """Two prompts is the whole promise of this path. A third value added without a
    decision is the kind of thing that turns a two-prompt install into a form."""
    user_config = load(".claude-plugin/plugin.json")["userConfig"]
    assert set(user_config) == {"address", "token"}
    for key, field in user_config.items():
        assert field["type"] == "string", key
        assert field["title"], key
        assert field["description"], key
        assert field["required"] is True, key


def test_the_token_is_marked_sensitive() -> None:
    """`sensitive` is what masks the input and keeps the value out of settings.json, into
    secure storage instead. Without it the token lands in a plain configuration file."""
    token = load(".claude-plugin/plugin.json")["userConfig"]["token"]
    assert token["sensitive"] is True


def test_the_mcp_server_takes_both_values_by_substitution() -> None:
    servers = load(".mcp.json")["mcpServers"]
    assert set(servers) == {"glosswork"}
    server = servers["glosswork"]
    assert server["type"] == "http"
    assert server["url"] == "${user_config.address}"
    assert server["headers"]["Authorization"] == "Bearer ${user_config.token}"


def test_the_agent_label_names_this_harness() -> None:
    """The label is what a person reads in the workspace's history to see which tool made
    a change, so the plugin's own calls are labeled for the harness it installs into."""
    servers = load(".mcp.json")["mcpServers"]
    assert servers["glosswork"]["headers"]["X-Agent-Label"] == "claude-code"


def test_every_substituted_value_is_declared() -> None:
    """A substitution naming a key the manifest does not declare is never filled in, and
    the server receives the literal text instead of the value."""
    declared = set(load(".claude-plugin/plugin.json")["userConfig"])
    referenced = set(SUBSTITUTION.findall((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8")))
    assert referenced, ".mcp.json substitutes nothing, so it asks the person for nothing"
    assert referenced <= declared, f"undeclared: {sorted(referenced - declared)}"
