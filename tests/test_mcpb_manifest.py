"""The Claude Desktop extension's manifest: what it asks for, and what it runs.

Structural only. Its input is the files in `mcpb/`, never a running system. What the
bundle actually does against a workspace is `tests/test_mcpb_bundle.py`, which needs
Docker and Node and so is marked `harness` and excluded from CI.
"""

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MCPB = REPO_ROOT / "mcpb"

MANIFEST_PATH = MCPB / "manifest.json"
PACKAGE_PATH = MCPB / "package.json"
LOCKFILE_PATH = MCPB / "package-lock.json"
BUILD_SCRIPT_PATH = MCPB / "build.sh"

# A bare version: digits and dots, no `^`, `~`, `*`, no range, no tag, no URL. An
# extension is installed once and run for months, so the tree it ships has to be the
# tree that was measured.
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")

# The token reaches the proxy as `${GLOSSWORK_TOKEN}`, substituted by the proxy itself
# from its environment. Anything that looks like the value rather than the reference is
# the failure non-negotiable 7 exists for.
TOKEN_ENVIRONMENT_VARIABLE = "GLOSSWORK_TOKEN"

# Q51 accepts one cost for reaching a workspace on the person's own network: on a plain
# HTTP address the bearer token crosses that network readable. The warning is part of
# the feature. These are the three things it cannot be written without saying.
CLEAR_TEXT_WARNING_TERMS = ("clear text", "network", "token")

WARNING_BEARERS = ("README.md", "mcpb/README.md")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest() -> Any:
    return load(MANIFEST_PATH)


def server_args() -> list[str]:
    return list(manifest()["server"]["mcp_config"]["args"])


def missing_warning_terms(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in CLEAR_TEXT_WARNING_TERMS if term not in lowered]


def test_the_manifest_is_a_node_extension() -> None:
    document = manifest()
    assert document["manifest_version"], "no manifest_version"
    assert document["name"] == "glosswork"
    assert document["server"]["type"] == "node"
    entry_point = document["server"]["entry_point"]
    assert entry_point == "node_modules/mcp-remote/dist/proxy.js", entry_point


def test_the_extension_asks_for_the_address_and_the_token_and_nothing_else() -> None:
    """Two values is the whole promise of this path. A third turns an install into a
    form, and the item's "Done when" names the two by name."""
    user_config = manifest()["user_config"]
    assert set(user_config) == {"address", "token"}
    for key, field in user_config.items():
        assert field["type"] == "string", key
        assert field["title"], key
        assert field["description"], key
        assert field["required"] is True, key


def test_the_token_is_marked_sensitive() -> None:
    """`sensitive` is what masks the field and sends the value to the operating
    system's secure storage instead of a plain configuration file."""
    assert manifest()["user_config"]["token"]["sensitive"] is True


def test_the_token_reaches_the_proxy_by_environment_and_never_by_argument() -> None:
    """Non-negotiable 7. An argument list is readable by every process on the machine;
    an environment is not. The argument holds the reference, the environment the value."""
    mcp_config = manifest()["server"]["mcp_config"]
    assert mcp_config["env"] == {TOKEN_ENVIRONMENT_VARIABLE: "${user_config.token}"}
    for argument in mcp_config["args"]:
        assert "${user_config.token}" not in argument, argument


def test_the_address_the_person_types_is_the_address_the_proxy_is_given() -> None:
    assert "${user_config.address}" in server_args()


def test_the_proxy_is_allowed_to_reach_a_plain_http_address() -> None:
    """Q51, 2026-09-18. Without this flag `mcp-remote` refuses any plain HTTP address
    whose host is not the literal string `localhost` or `127.0.0.1`, so a workspace on
    the person's own network is unreachable by anything they could type."""
    assert "--allow-http" in server_args()


def test_the_transport_is_streamable_http_only() -> None:
    """`http-only` stops the proxy falling back to SSE and stops it spending a startup
    probing for a transport the product does not serve."""
    args = server_args()
    assert "--transport" in args
    assert args[args.index("--transport") + 1] == "http-only"


def test_every_request_carries_the_token_and_the_agent_label() -> None:
    """The label is what a person reads in the workspace's history to see which tool
    made a change. `mcp-remote` splits a header argument on the first colon, so neither
    of these carries a space after it."""
    args = server_args()
    headers = [args[index + 1] for index, value in enumerate(args) if value == "--header"]
    assert "Authorization:Bearer ${" + TOKEN_ENVIRONMENT_VARIABLE + "}" in headers
    assert "X-Agent-Label:claude-desktop" in headers


def test_the_manifest_names_no_host() -> None:
    """Non-negotiable 3. A change of host must never be a change to a manifest."""
    document = manifest()
    assert "repository" not in document
    assert "homepage" not in document
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    assert "gitlab.com" not in text
    assert "github.com" not in text


def test_the_manifest_declares_no_compatibility_block() -> None:
    """D4, answered 2026-09-18. Nothing in the bundle is platform specific: it is Node
    and one pinned npm package. Declaring the one platform that was measured would stop
    the extension installing for a pilot on Windows for no measured reason, and the
    README is where "only macOS was measured" belongs."""
    assert "compatibility" not in manifest()


def test_the_proxy_is_pinned_to_an_exact_version() -> None:
    dependencies = load(PACKAGE_PATH)["dependencies"]
    assert set(dependencies) == {"mcp-remote"}, dependencies
    assert EXACT_VERSION.match(dependencies["mcp-remote"]), dependencies["mcp-remote"]


def test_the_lockfile_pins_the_same_proxy_version() -> None:
    """`package.json` pins the one dependency; the lockfile pins its whole tree. A
    lockfile that has drifted from the pin means `npm ci` builds something else."""
    pinned = load(PACKAGE_PATH)["dependencies"]["mcp-remote"]
    packages = load(LOCKFILE_PATH)["packages"]
    locked = packages["node_modules/mcp-remote"]["version"]
    assert locked == pinned, f"lockfile has {locked}, package.json pins {pinned}"


def test_the_build_script_pins_the_packer() -> None:
    """`npx --yes @anthropic-ai/mcpb` with no version fetches whatever is current, so
    the tool that builds the bundle would move without anyone choosing it."""
    text = BUILD_SCRIPT_PATH.read_text(encoding="utf-8")
    found = re.search(r'^MCPB_VERSION="([^"]+)"', text, re.MULTILINE)
    assert found, "build.sh declares no MCPB_VERSION"
    assert EXACT_VERSION.match(found.group(1)), found.group(1)
    assert "@anthropic-ai/mcpb@${MCPB_VERSION}" in text


def test_the_substituted_token_is_not_mistaken_for_a_literal() -> None:
    """The reference form must not trip the credential scanner, or the only correct way
    to pass a token would be the one tests/test_no_credentials.py forbids."""
    spec = importlib.util.spec_from_file_location(
        "conn_no_credentials", Path(__file__).with_name("test_no_credentials.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    literal = module.CREDENTIAL_PATTERNS["Literal bearer credential"]
    assert not literal.search("Bearer ${" + TOKEN_ENVIRONMENT_VARIABLE + "}")
    assert not literal.search(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_the_address_field_warns_that_a_network_address_sends_the_token_in_clear_text() -> None:
    """Q51's accepted cost, stated where the person is when they choose an address.
    The field description is the only text Claude Desktop shows at that moment."""
    description = manifest()["user_config"]["address"]["description"]
    missing = missing_warning_terms(description)
    assert not missing, f"the address description does not say: {missing}"


def test_the_readme_warns_that_a_network_address_sends_the_token_in_clear_text() -> None:
    """Q51 makes this a build requirement rather than documentation that can follow
    later: the extension reaches the network because the warning ships with it."""
    for relative in WARNING_BEARERS:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        missing = missing_warning_terms(text)
        assert not missing, f"{relative} does not say: {missing}"


def test_the_address_field_says_the_spelling_must_match_the_workspace() -> None:
    """The product matches the MCP `Host` header against an exact `host:port`, so
    `localhost` and `127.0.0.1` are different addresses and the wrong one answers
    `421 Invalid Host header`, which names neither the address nor the fix."""
    description = manifest()["user_config"]["address"]["description"].lower()
    assert "localhost" in description
    assert "127.0.0.1" in description
    assert "/mcp" in description
