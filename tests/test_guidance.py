"""The schema skill is the approved guidance text, and nothing else.

The original lives in the Glosswork product repository, which serves it through the MCP
server's own prompts. The copy in `skills/glosswork-schema-design/SKILL.md` is the second
channel, for harnesses that load skills but do not surface prompts. Until the product
repository's copy merges, the approved text is pinned here by hash.

These hashes change only in the change that re-pins them to a new approved original. Never
change a hash to match an edited copy: fix the original, then re-pin.
"""

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIRECTORY = REPO_ROOT / "skills" / "glosswork-schema-design"
SKILL_FILE = SKILL_DIRECTORY / "SKILL.md"

# SHA-256 of the approved front matter, from its first `---` line through its second,
# including the newline that ends the second.
APPROVED_FRONT_MATTER_SHA256 = "b842aa4e5a8db6f232080a2ed09810ba048ebd885e8f16d430f40c4989599d60"

# SHA-256 of the approved body: everything after the front matter and its one empty line.
APPROVED_BODY_SHA256 = "bc84778a3343b975287cbfc14be0262bebbf822c8f56262d55adf5749717d74c"

DESCRIPTION_LIMIT = 1024  # Agent Skills specification


def split_skill(text: str) -> tuple[str, str]:
    """Return the front matter block and the body, which one empty line separates."""
    assert text.startswith("---\n"), "SKILL.md does not open with a front matter line"
    closing = text.index("\n---\n", 3) + len("\n---\n")
    front_matter, rest = text[:closing], text[closing:]
    assert rest.startswith("\n"), "SKILL.md has no empty line between front matter and body"
    return front_matter, rest[1:]


def front_matter_value(front_matter: str, key: str) -> str:
    for line in front_matter.splitlines():
        if line.startswith(f"{key}:"):
            return line[len(key) + 1 :].strip()
    raise AssertionError(f"the front matter declares no {key}")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_skill_body_is_the_approved_text() -> None:
    _, body = split_skill(SKILL_FILE.read_text(encoding="utf-8"))
    assert sha256(body) == APPROVED_BODY_SHA256, (
        "the SKILL.md body drifted from the approved guidance text; fix the original"
    )


def test_the_skill_front_matter_is_the_approved_text() -> None:
    front_matter, _ = split_skill(SKILL_FILE.read_text(encoding="utf-8"))
    assert sha256(front_matter) == APPROVED_FRONT_MATTER_SHA256, (
        "the SKILL.md front matter drifted from the approved text; fix the original"
    )


def test_the_skill_name_is_its_folder_name() -> None:
    front_matter, _ = split_skill(SKILL_FILE.read_text(encoding="utf-8"))
    assert front_matter_value(front_matter, "name") == SKILL_DIRECTORY.name


def test_the_skill_description_fits_the_specification() -> None:
    front_matter, _ = split_skill(SKILL_FILE.read_text(encoding="utf-8"))
    description = front_matter_value(front_matter, "description")
    assert description
    assert len(description) <= DESCRIPTION_LIMIT
