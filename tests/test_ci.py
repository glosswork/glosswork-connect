"""CI: one workflow on GitHub Actions, with the checks this repository depends on.

`main` is protected with the `lint`, `test` and `secrets` checks required. A required check
is named by its job id, so a renamed job silently stops being required. These tests pin the
names, and the steps each job must run, so that a change to the workflow that drops a check
fails here first.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def workflow_text() -> str:
    assert WORKFLOW.is_file(), ".github/workflows/ci.yml is missing"
    return WORKFLOW.read_text(encoding="utf-8")


def job_ids() -> list[str]:
    """The keys directly under `jobs:`, read by indentation. The workflow has no other
    mapping at two spaces under `jobs:`, and this avoids a YAML dependency."""
    ids: list[str] = []
    in_jobs = False
    for line in workflow_text().splitlines():
        if line.startswith("jobs:"):
            in_jobs = True
            continue
        if in_jobs and line and not line.startswith(" ") and not line.startswith("#"):
            break
        if in_jobs and line.startswith("  ") and not line.startswith("   "):
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith("#"):
                ids.append(stripped[:-1])
    return ids


def test_there_is_no_gitlab_ci_file() -> None:
    assert not (REPO_ROOT / ".gitlab-ci.yml").exists()


def test_the_jobs_are_exactly_the_required_checks() -> None:
    assert job_ids() == ["lint", "test", "secrets"]


def test_lint_runs_both_halves_as_separate_steps() -> None:
    lines = [line.strip() for line in workflow_text().splitlines()]
    assert "- run: uv run --frozen ruff check ." in lines
    assert "- run: uv run --frozen ruff format --check ." in lines


def test_the_tests_run() -> None:
    assert "- run: uv run --frozen pytest -q" in [
        line.strip() for line in workflow_text().splitlines()
    ]


def test_gitleaks_runs_from_a_checksum_verified_download_and_fails_on_a_finding() -> None:
    text = workflow_text()
    assert "sha256sum -c" in text
    assert "gitleaks" in text and "git . " in text
    assert "--exit-code 1" in text


def test_every_commit_is_checked_for_the_company_identity() -> None:
    text = workflow_text()
    assert "git log --format='%ae%n%ce'" in text
    assert "-e hello@glosswork.dev" in text


def test_the_identity_check_skips_only_the_temporary_merge_commit() -> None:
    """A pull request run examines the pull request's own commits, HEAD^1..HEAD^2, after
    proving HEAD^2 is the pull request's head. Every other known event examines the whole
    history, and an unknown event, a shallow checkout or an empty range fails."""
    text = workflow_text()
    assert "fetch-depth: 0" in text
    assert "git rev-parse --is-shallow-repository" in text
    assert '"$second" != "$PR_HEAD_SHA"' in text
    assert "range='HEAD^1..HEAD^2'" in text
    assert "push | workflow_dispatch)" in text
    assert "range='HEAD'" in text
    assert "so it fails rather than pass unchecked" in text
    assert 'if [ "$examined" -eq 0 ]; then' in text
    assert "grep -v -x -e hello@glosswork.dev -e noreply@github.com || true" in text
    assert text.count("glosswork.dev") == text.count("hello@glosswork.dev")


def test_a_run_can_be_started_by_hand() -> None:
    assert "workflow_dispatch:" in workflow_text()
