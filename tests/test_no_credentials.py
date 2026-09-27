"""No credential ever enters this repository.

People install this kit. A token committed here would be handed to everyone who clones
it, and a kit that leaks its own credentials is the worst defect this repository can ship.
Values come from the person at install time and are substituted by the harness.

The patterns below are assembled from fragments on purpose, so that this file does not
itself contain a token-shaped string and trip the rule it enforces.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".cache",
}

CREDENTIAL_PATTERNS = {
    "Glosswork access token": re.compile("gw" + "_pat_" + r"[A-Za-z0-9_\-]{8,}"),
    "Glosswork upload token": re.compile("gw" + "_upl_" + r"[A-Za-z0-9_\-]{8,}"),
    "Anthropic API key": re.compile("sk-" + "ant-" + r"[A-Za-z0-9_\-]{8,}"),
    "GitLab personal access token": re.compile("glpat" + "-" + r"[A-Za-z0-9_\-]{16,}"),
    # Classic tokens and OAuth, user-to-server, server-to-server and refresh tokens share
    # one shape: a `gh` prefix, one letter, an underscore and 36 alphanumerics.
    "GitHub token": re.compile("gh" + "[pousr]_" + r"[A-Za-z0-9]{36}"),
    "GitHub fine-grained personal access token": re.compile(
        "github" + "_pat_" + r"[A-Za-z0-9_]{22,}"
    ),
    "AWS access key id": re.compile("AKIA" + r"[0-9A-Z]{16}"),
    "Private key block": re.compile("-----BEGIN" + r"[ A-Z]*" + "PRIVATE KEY"),
    # A bearer value spelled out rather than substituted. `${user_config.token}` does not
    # match: the character class stops at the opening brace.
    "Literal bearer credential": re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{20,}"),
}


def tracked_text_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if SKIP_DIRECTORIES & set(path.relative_to(REPO_ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def test_the_scan_actually_reads_something() -> None:
    """A scan that walks an empty list passes by construction and proves nothing."""
    assert len(tracked_text_files()) > 10


def test_no_file_holds_anything_token_shaped() -> None:
    findings: list[str] = []
    for path in tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue  # Binary. Secret detection in CI covers what this cannot read.
        for description, pattern in CREDENTIAL_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(REPO_ROOT)}: {description}")
    assert not findings, "credential shaped strings found: " + "; ".join(findings)


def test_the_patterns_can_fail() -> None:
    """Every assertion must be able to fail. These patterns are the load-bearing part of
    this file, so each one is measured against a value it must catch."""
    samples = {
        "Glosswork access token": "gw" + "_pat_" + "A1b2C3d4E5f6",
        "Glosswork upload token": "gw" + "_upl_" + "A1b2C3d4E5f6",
        "Anthropic API key": "sk-" + "ant-" + "A1b2C3d4E5f6",
        "GitLab personal access token": "glpat" + "-" + "A1b2C3d4E5f6g7h8",
        "GitHub token": "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
        "GitHub fine-grained personal access token": "github" + "_pat_" + "A1b2C3d4E5f6G7h8I9j0K1",
        "AWS access key id": "AKIA" + "ABCDEFGHIJKLMNOP",
        "Private key block": "-----BEGIN" + " RSA " + "PRIVATE KEY" + "-----",
        "Literal bearer credential": "Bearer " + "A1b2C3d4E5f6G7h8I9j0K1l2",
    }
    for description, pattern in CREDENTIAL_PATTERNS.items():
        assert pattern.search(samples[description]), f"{description} matches nothing"


def test_the_substituted_token_is_not_mistaken_for_a_literal() -> None:
    """The manifest's own `Bearer ${user_config.token}` must not trip the rule, or the
    only correct way to pass a token would be the one the tests forbid."""
    assert not CREDENTIAL_PATTERNS["Literal bearer credential"].search(
        "Bearer ${user_config.token}"
    )
