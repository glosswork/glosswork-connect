# 001: the public kit says what is true, ships only what it runs, and its tests guard what they claim to

| | |
| --- | --- |
| Issue | #1 (to be filed after plan approval) |
| Branch | `1-public-kit-cleanup` |
| Depends on | Nothing to merge first. Two values from the maintainer before the build starts: the Claude Desktop version the extension was installed in, and the answer to the decision in "What changes", item 6 |

This is GitHub change 1. It is not "archive 001", which was numbered by the private archive
(see `docs/changes/README.md`). Issue and pull request numbers share one sequence on GitHub,
and on 2026-10-02 the repository had no issue and no pull request, so the next number is 1.
If anything else takes number 1 before this issue is filed, the branch and this file are
renamed to the number the issue actually gets, before anything is pushed.

## Why

The repository became public on 2026-10-02. A stranger who reads it today finds text that
was true while it was private and is not now, a personal image name, a person's first name
where the maintainer is meant, instructions that disagree with how the plugin is actually
installed, a Claude Desktop extension that ships its own build script, and two tests that
guard less than their names say. None of it is a leaked credential, and none of it stops the
kit from working. All of it is what a careful reader judges the kit by.

The changes are small and touch the same few files, so they go in one change rather than
several, each of which would carry a full plan, review and pull request of its own.

## Premises

Every premise below was established on 2026-10-02 in a fresh clone of
`https://github.com/glosswork/glosswork-connect` at `12a23ad` (the only commit), on macOS
(arm64) with uv 0.9.18, Node 22.17.1, npm 10.9.2, Docker 28.4.0, gitleaks 8.30.1 and Claude
Code 2.1.287 (the current npm release, `npm view @anthropic-ai/claude-code version`, read
2026-10-02). Every Claude Code command ran under `env -i` with a scratch `HOME` and a scratch
`CLAUDE_CONFIG_DIR`. Nothing in a real Claude Code configuration was read or written.

**P1. The README says things that stopped being true when the repository went public.**
Read in `README.md`: lines 7 to 8 say the repository "is private until the site is live" and
that installs come "from a local clone or from a file sent to them"; line 14 says the
marketplace is "added from a local clone"; line 37 tells the reader to run
`claude plugin marketplace add <path to a clone of this repository>`; lines 17 and 65 to 68
say the extension has not been installed in Claude Desktop. `.github/ISSUE_TEMPLATE/bug.md`
line 19 asks whether the install came from "a local clone, or a file that was sent". The
Claude Desktop install was made by the maintainer on 2026-10-02; that is the maintainer's
statement, not a measurement this change made, and the Claude Desktop version is not yet
known (see Depends on).

**P2. The marketplace installs from GitHub by its short name, and that install copies only
the repository's files.** Measured: `claude plugin marketplace add glosswork/glosswork-connect`
exits 0 ("cloning via HTTPS"), `claude plugin install glosswork@glosswork --scope user` exits
0 and reports the two unset values. The plugin's copy in the scratch configuration directory
holds 36 files, 244 KB, which is exactly `git ls-files | wc -l` (36). No `.venv`,
`.pytest_cache`, `.ruff_cache` or `.git`.

**P3. Added from a working clone, the marketplace copies the whole directory, untracked files
included.** Measured: in a clone where `uv sync --frozen` and `uv run pytest -q` had run, the
same two commands with the clone's path copied 702 files, 31 MB, into
`plugins/cache/glosswork/glosswork/0.2.0/` of the scratch configuration directory, including
`.venv`, `.pytest_cache` and `.ruff_cache`, all three of which `.gitignore` names. Only `.git`
was left out. So any untracked file in a clone, a stray token file included, would be copied
into the person's Claude Code configuration directory. Nothing in the kit can make a local
directory install skip files, so the fix is to tell people to add the marketplace from GitHub,
and to say why.

**P4. Inside a clone of the kit, Claude Code offers the plugin's own server again as a project
server, and approving it would send a literal placeholder.** The repository root is the plugin
root, so its `.mcp.json` is also a project-scope MCP configuration for any Claude Code session
started there. Measured in a fresh Linux container (`node:22-bookworm`, Claude Code 2.1.287,
installed from GitHub, values set with `claude plugin configure --values-stdin` and a
placeholder token, so no keychain was involved): `claude mcp list` from the clone's root lists
`plugin:glosswork:glosswork` and also `glosswork: ${user_config.address} (HTTP) - Pending
approval`. From `/` it lists only the plugin's server. On macOS with the plugin installed and
not configured, the same `glosswork: ${user_config.address}` line appears from the clone root
and nothing appears outside it.

**P5. Moving the server into `plugin.json` would remove that line, but would change the
plugin's shape.** Measured in a scratch copy: with `.mcp.json`'s `mcpServers` moved into
`.claude-plugin/plugin.json` and `.mcp.json` deleted, `claude plugin validate . --strict`
exits 0 and `claude mcp list` from the clone root lists no project server. Not measured: that
the plugin's server then connects to a real workspace with the person's two values. Three
tests and two documents name `.mcp.json` (`tests/test_manifests.py` lines 67, 78 and 86,
`tests/test_layout.py` line 43, `AGENTS.md`, `README.md`).

**P6. `claude plugin validate` writes into the Claude Code configuration directory.**
Measured: `claude plugin validate . --strict` under `env -i` with a scratch
`CLAUDE_CONFIG_DIR` exits 0 ("Validation passed") and leaves a `.claude.json` and a backup of
it in that directory. Run without a scratch directory, it would write to the person's own
Claude Code configuration. `AGENTS.md` line 22 gives the command bare.

**P7. Claude Code copies `docs/changes/` into the configuration directory.** Measured with P2
and P3: `docs/changes/` is present in the plugin's copy either way. So a plan file that wrote
the access token's prefix literally would land in every installing person's configuration
directory, and a check that searches a configuration directory for that prefix to find where
a token was stored would match the plan instead. `git grep -n` for the bare prefix exits 1
today: the tests assemble it from fragments, and nothing writes it whole.

**P8. A raw terminal capture of Claude Code's screen does not show what was on the screen.**
Inherited from archive 001, not re-measured here. An attempt to capture Claude Code 2.1.287's
first screen in a Linux container under `script` hung with an empty capture and was stopped.
The build re-measures it (checklist step 9) before AGENTS.md states it with a version.

**P9. The README's paragraph on Claude's own connector dialog asks for a second header that
should not be sent.** Read at `README.md` line 29: "with the agent label as a second header".
The maintainer found, before this repository was public, that the dialog takes the address
and the token and nothing else, and a second header with the label's name is refused when the
connector is added. The label travels on the token itself, which README line 60 already
describes. That finding is the maintainer's, not this change's, and was not repeated here
because the dialog needs a signed-in Claude account. `grep -n "second header" README.md`
exits 0 today.

**P10. A personal image name is written in three places, and the harness tests cannot run
with it.** Read: `pyproject.toml` line 37 and `tests/test_mcpb_bundle.py` lines 6 and 43 name
an older image under a personal namespace. Measured: that image is not present on the
development machine, so `GLOSSWORK_HARNESS=1 uv run pytest -q -m harness` on unchanged `main`
exits 1 with 16 errors, each "harness prerequisite missing ... the image ... is not present".
With only the image constant changed to `docker.io/glosswork/glosswork:0.1.0` (the public
release, tag `0.1.0` active for amd64 and arm64 on Docker Hub, last updated 2026-09-29, read
2026-10-02), the same command exits 0: 16 passed. The name also stays in the history of
commit `12a23ad`; this change removes it from the tree only.

**P11. CONTRIBUTING names a person where it means the maintainer.** Read at `CONTRIBUTING.md`
lines 12, 48 and 58. `LICENSE` already names the company, Heavylift Labs LLC, and the three
manifests name Heavylift Labs as author.

**P12. The commit identity rule already holds, and CI enforces it.** Measured:
`git log --format='%ae%n%ce' | sort -u` prints only `hello@glosswork.dev`. Read at
`.github/workflows/ci.yml` lines 81 to 87: the `secrets` job fails on any commit whose author
or committer is not `hello@glosswork.dev` or GitHub's own web-merge committer. This change
keeps it true by committing as `hello@glosswork.dev` (set in this clone's local config).

**P13. Secret detection already fails CI on a finding.** Read at `ci.yml` lines 66 to 80: the
`secrets` job downloads gitleaks 8.30.1, checks it against a SHA-256 that matches the
published `gitleaks_8.30.1_checksums.txt` entry for `linux_x64` (verified 2026-10-02), and
runs `gitleaks git . --redact --no-banner --exit-code 1` over the full history
(`fetch-depth: 0`). No step or job sets `continue-on-error`, so a failing step fails the job.
Mutation, in a scratch clone whose remote was removed and which was never pushed: the same
gitleaks command on the clean history exits 0 ("no leaks found"); after committing one file
holding a randomly generated string in GitHub's personal-token shape, it exits 1 with one
finding, rule `github-pat`, secret redacted; `tests/test_no_credentials.py` also fails on it
(1 failed, 3 passed). The last CI run on `main` (`12a23ad`, run 36285380840) passed `lint`,
`test` and `secrets`. Read through the API's branch endpoint: `main` is protected, with
required checks `lint`, `test` and `secrets` and enforcement level `everyone`. What is missing
is that CONTRIBUTING does not say what the `secrets` check does.

**P14. The workflow's comment about GitHub's own scanning is out of date.** Read at `ci.yml`
lines 58 to 61: GitHub secret scanning "is not available to a private repository on this plan
without a paid add-on, so this is the scanner until the repository is public". Whether GitHub
secret scanning and push protection are now on is not readable with a non-admin token
(`security_and_analysis` reads null, the alerts endpoint 404). GitHub's documentation (read
2026-10-02) puts both under Settings, Advanced Security, Secret Protection.

**P15. The Claude Desktop bundle ships its build script and its README.** Measured: after
`bash mcpb/build.sh` (mcpb 2.1.2), the bundle holds 729 files; outside `node_modules/` they
are `README.md`, `build.sh`, `manifest.json` and `package.json`. `mcpb/package-lock.json` is
already left out by the packer; npm's own `node_modules/.package-lock.json` ships.

**P16. An unanchored ignore pattern strips files the proxy's dependencies carry.** Measured
in a scratch build: an `mcpb/.mcpbignore` of `build.sh`, `README.md`, `package-lock.json`
shrinks the bundle to 645 files, because `README.md` also matches 83 readme files inside
`node_modules/`, case-insensitively. Anchored as `/build.sh`, `/README.md`,
`/package-lock.json`, the bundle holds 727 files: exactly the 729 minus the root `README.md`
and `build.sh`, `node_modules/mcp-remote/README.md` still present, and the `.mcpbignore` file
itself not shipped. With the anchored file and the public image, the full harness suite
passes (16 passed, exit 0).

**P17. The packer does not rewrite the manifest.** Measured: `cmp` of the `manifest.json`
inside the built bundle with `mcpb/manifest.json` exits 0, with and without the ignore file.
No test asserts it today: the harness tests read the bundle's own argument list, and the tie
to the source manifest was checked by hand once.

**P18. The README warning test passes with the warning deleted.** Read at
`tests/test_mcpb_manifest.py` lines 35 and 188 to 194: it checks that `clear text`, `network`
and `token` each appear anywhere in `README.md` and `mcpb/README.md`. Mutation, in a scratch
clone: deleting the whole warning paragraph (`README.md` lines 92 to 96) leaves the test
passing (1 passed), because line 17's table cell also says "clear text", and the other two
words occur throughout.

**P19. The plan file itself fails one test while it exists.** Read at `tests/test_layout.py`
line 46: `docs/changes/` may hold only its README. That is deliberate, and it means
`uv run pytest -q` exits 1 on this branch until the closeout commit deletes this file.

**P20. Baseline.** Measured on unchanged `main`: `uv sync --frozen` exit 0; `uv run pytest -q`
exit 0, 69 passed, 16 deselected; `uv run ruff check .` exit 0; `uv run ruff format --check .`
exit 0.

## What changes

1. **`README.md`.**
   - Lines 7 to 8 are deleted. Nothing replaces them: the "Connecting" sections say how to
     install.
   - Line 14: the marketplace is "added from GitHub as `glosswork/glosswork-connect`", with
     its status giving the Claude Code version it was measured on in this change.
   - Line 37, step 1 becomes `claude plugin marketplace add glosswork/glosswork-connect`.
     Directly after the steps, a short paragraph: add it from GitHub, not from a working
     clone, because Claude Code (version named) copies a local directory whole into its
     configuration directory, untracked files included, while the GitHub source copies only
     the repository's files.
   - Line 29: "paste the address, then paste the token as an `Authorization` header" and
     nothing about a second header. The label rides on the token, as line 60 already says.
   - Lines 17 and 65 to 68: the "not installed in Claude Desktop" statements are replaced by
     what is true: installed in Claude Desktop (version supplied by the maintainer) on macOS
     on 2026-10-02, with the harness measurements of 2026-09-18 still credited to the harness
     tests. If the maintainer does not supply a version, the README says it was installed on
     that date and names no version, and the plan records that as a deviation.
   - The Claude Code connection claims that were measured on 2.1.274 (Keychain storage, the
     masked field, survival across restart) keep their 2.1.274 label. This change re-measures
     only the install path and a connection on Linux (checklist step 10), and the README
     says exactly that and no more.
   - The bundle paragraph says `mcpb/.mcpbignore` keeps the build script and the README out
     of the bundle.

2. **`.github/ISSUE_TEMPLATE/bug.md` line 19** asks where the install came from: the GitHub
   marketplace, a clone (fresh or not), or a `.mcpb` built from which commit.

3. **`pyproject.toml` line 37 and `tests/test_mcpb_bundle.py` lines 6 and 43** name
   `docker.io/glosswork/glosswork:0.1.0`.

4. **`CONTRIBUTING.md`.** Line 12: "**Maintainer** means Heavylift Labs, which publishes
   Glosswork." Lines 48 and 58: "the maintainer merges". The "Branches and commits" section
   gains what the `secrets` check is: gitleaks 8.30.1, checksum-verified, over every commit
   in the pull request's history, failing on any finding, plus the commit identity check;
   and, once the maintainer has confirmed it (step 13), that GitHub secret scanning and push
   protection are on for the repository.

5. **`.github/workflows/ci.yml` lines 55 to 61.** The comment stops saying GitHub scanning is
   unavailable until the repository is public. It says gitleaks in CI is the gate a pull
   request cannot pass without, and that GitHub's own secret scanning and push protection
   are repository settings, described in CONTRIBUTING. No step changes.

6. **`AGENTS.md`.**
   - Commands: the validate row becomes
     `env -i PATH="$PATH" HOME="$(mktemp -d)" CLAUDE_CONFIG_DIR="$(mktemp -d)" claude plugin validate . --strict`,
     with one sentence on why (P6), naming the Claude Code version.
   - Traps, three new entries, each naming the Claude Code version measured:
     (a) a raw terminal capture of Claude Code's screen cannot prove what it showed, so a
     screen is rendered through a terminal emulator before anyone reads it (P8, re-measured
     in step 9);
     (b) Claude Code copies the whole plugin directory, `docs/changes/` included, into the
     configuration directory, so no file in this repository writes the token prefix whole
     (P7);
     (c) a Claude Code session started in a clone of this repository offers the plugin's
     `.mcp.json` as a project server with a literal `${user_config.address}`; do not approve
     it (P4).
   - **Decision for the maintainer.** Trap (c) satisfies the requirement. The alternative is
     to move the server into `.claude-plugin/plugin.json` and delete `.mcp.json` (P5), which
     removes the prompt for anyone who clones the kit, but changes the plugin's shape, three
     tests and two documents, and needs a real connection re-proven. **Recommended: the trap
     in this change**, and the move as its own later change if contributors hit the prompt,
     because this change is about text and tests, and the move is a behavior change to the
     one piece that already works for strangers.

7. **`mcpb/.mcpbignore`** (new): `/build.sh`, `/README.md` and `/package-lock.json`, each
   anchored to the bundle root (P16). The last is already excluded by the packer and is
   listed so the intent survives a packer change.

8. **Tests.**
   - `tests/test_mcpb_manifest.py`: the README warning test asserts the warning sentence
     itself. Each file's text, with whitespace collapsed, must contain its exact warning
     sentence: in `README.md`, "A plain `http://` address that is not on this machine sends
     the token across the network in clear text."; in `mcpb/README.md`, the heading "A plain
     HTTP address on your network sends the token in clear text". The three-word check is
     retired for the two READMEs and kept for the manifest's address description, which
     has its own test and is not in scope.
   - `tests/test_mcpb_manifest.py`: a structural test that `mcpb/.mcpbignore` exists and its
     non-comment lines are exactly the three anchored patterns.
   - `tests/test_mcpb_bundle.py` (harness): the bundle's root entries, those with no `/`, are
     exactly `manifest.json` and `package.json`, and `node_modules/mcp-remote/README.md` is
     present (the guard against an unanchored pattern).
   - `tests/test_mcpb_bundle.py` (harness): the `manifest.json` inside the built bundle is
     byte-identical to `mcpb/manifest.json`.
   - `tests/test_license_and_readme.py`: the README names
     `claude plugin marketplace add glosswork/glosswork-connect`, does not contain
     `<path to a clone`, and does not contain "second header", "private until" or
     "installed in Claude Desktop yet".

## What does not change

- No behavior of the plugin, `.mcp.json`, `.claude-plugin/`, `mcpb/manifest.json`,
  `mcpb/package.json`, `mcpb/build.sh`, the skills, or the guidance hashes. So
  `claude plugin validate` is run as a local fence, not as evidence of a change.
- The CI jobs and their ids (`lint`, `test`, `secrets`), their steps and the pinned gitleaks
  version and checksum. Only a comment in `ci.yml` changes.
- The README statements measured on Claude Code 2.1.274 keep that version.
- The history. Commit `12a23ad` keeps the personal image name and the first name it already
  carries; removing them from history would mean rewriting a public `main`, which is outside
  this change and is the maintainer's call.
- Text deliberately left: `docs/changes/README.md`'s note on the private archive, the
  README's "kept in a private archive" line, and the generic references to early users in
  AGENTS.md and the Change template, none of which names anyone.
- No new test scans for the personal names, because a public test would have to spell them.
  The Accept block checks them with `git grep` instead.

## Constraints

- Every commit is authored and committed as `Glosswork <hello@glosswork.dev>`, with no
  session or co-author trailer.
- Nothing is pushed until the closeout, once. No issue, pull request or comment is posted on
  GitHub before the maintainer approves its wording.
- No GitHub setting is changed by an agent. Step 13 is the maintainer's.
- No file writes the access token's prefix whole, including this plan.
- Claude Code commands run under `env -i` with a scratch `HOME` and `CLAUDE_CONFIG_DIR`. Any
  step that stores a token runs in a Linux container, so no macOS keychain item is written.
- Harness runs use a scratch workspace from `docker.io/glosswork/glosswork:0.1.0`, which the
  tests start and remove. They never point at a real workspace.
- `mcpb/dist/` is deleted before every harness run in this change, because the bundle fixture
  reuses an existing bundle.
- README text a stranger reads stays plain and claims nothing the kit has not measured. No em
  dashes.
- The full suite's exit code is read with `test_the_change_plan_directory_holds_only_its_readme`
  deselected until the closeout deletes this file, and in full after it (P19).

## Checklist

1. Write the new and changed assertions of "What changes" item 8, and the image constant
   only, then run them against the otherwise unchanged tree and record how each fails:
   - `uv run pytest -q tests/test_license_and_readme.py`: fails on the marketplace command,
     the clone path and the three stale phrases.
   - `uv run pytest -q tests/test_mcpb_manifest.py`: the `.mcpbignore` test fails (no file).
     The new warning-sentence test passes on `main`, which is expected; its proof is the
     mutation in step 6.
   - `rm -rf mcpb/dist && GLOSSWORK_HARNESS=1 uv run pytest -q -m harness`: the bundle
     root-entries test fails naming `README.md` and `build.sh`; the manifest identity test
     passes (P17), and its proof is the mutation in step 7.
2. Add `mcpb/.mcpbignore`. Rerun step 1's harness command: all pass.
3. Change `pyproject.toml` line 37 to the public image.
4. Edit `README.md` and `bug.md` as in items 1 and 2. Rerun `tests/test_license_and_readme.py`:
   passes.
5. Edit `CONTRIBUTING.md` and the `ci.yml` comment as in items 4 and 5 (the secret-scanning
   sentence waits for step 13).
6. Mutation for the warning test: delete `README.md`'s warning paragraph in a scratch copy;
   the new test fails and the old one, run from `main`, passes. Then replace the sentence with
   a rewording that keeps "network" and "token"; the new test fails. Record both.
7. Mutation for the manifest identity test: build, then change one byte of
   `mcpb/manifest.json` without rebuilding; the harness test fails. Restore and rerun: passes.
8. Mutation for the ignore file: replace the anchored patterns with unanchored ones,
   `rm -rf mcpb/dist`, run the harness bundle test; it fails on the missing
   `node_modules/mcp-remote/README.md`. Restore.
9. Re-measure the raw-capture trap on the then-current Claude Code: capture a Claude Code
   screen raw and rendered through a terminal emulator, in a Linux container, and record a
   line visible on the rendered screen that is absent from the raw capture verbatim. If it
   cannot be reproduced, the trap is written with the version it was last measured on and
   the deviation recorded.
10. In a Linux container with the then-current Claude Code: add the marketplace from GitHub,
    install, configure against a scratch workspace from the public image with a scratch
    token, and record `claude mcp list` showing the plugin's server connected. The README
    status for line 14 names that version.
11. Re-measure P2, P3 and P4 on the then-current Claude Code if it is newer than 2.1.287, and
    write the version measured into the README paragraph and the AGENTS.md traps.
12. Edit `AGENTS.md` as in item 6.
13. **The maintainer**, in the GitHub web page: Settings, Advanced Security, Secret
    Protection, Enable; then Push protection, Enable. Verify as an administrator with
    `gh api repos/glosswork/glosswork-connect --jq .security_and_analysis`, which should show
    `secret_scanning` and `secret_scanning_push_protection` with status `enabled`, or by
    screenshot of that settings page. Branch protection needs no action: the branch endpoint
    already shows `main` protected with `lint`, `test` and `secrets` required for everyone.
    The result goes in this plan's Deviations or into CONTRIBUTING as item 4 says.
14. Run the Accept block.

## Accept

Run from the repository root on the branch, with `UV_NO_CONFIG=1` exported. Each exit code is
read on its own, never through a pipe.

- **AC1. Lint, two commands.** `uv run --frozen ruff check .` exits 0, then
  `uv run --frozen ruff format --check .` exits 0.
- **AC2. The structural suite.**
  `uv run --frozen pytest -q --deselect tests/test_layout.py::test_the_change_plan_directory_holds_only_its_readme`
  exits 0, with more tests passing than the 69 on `main`.
- **AC3. The harness suite, against the public image.**
  `docker image inspect docker.io/glosswork/glosswork:0.1.0 >/dev/null` exits 0, then
  `rm -rf mcpb/dist && GLOSSWORK_HARNESS=1 uv run --frozen pytest -q -m harness` exits 0 with
  no skips.
- **AC4. The bundle ships only what it runs.** After AC3,
  `unzip -Z1 mcpb/dist/glosswork.mcpb > /tmp/kit-001-bundle.txt` exits 0, then
  `grep -c -v / /tmp/kit-001-bundle.txt` prints `2`, and
  `grep -x -e build.sh -e README.md -e package-lock.json /tmp/kit-001-bundle.txt` exits 1.
- **AC5. The stale text is gone.** Each of these exits 1:
  `grep -n "second header" README.md`;
  `grep -n -i "private until" README.md`;
  `grep -n "path to a clone" README.md`;
  `grep -n -i "installed in Claude Desktop yet" README.md`;
  `grep -n "until the repository is public" .github/workflows/ci.yml`.
  And `grep -n "claude plugin marketplace add glosswork/glosswork-connect" README.md` exits 0.
- **AC6. No personal identifier in the tree.** `git grep -n -i 'csch''eide'` exits 1, and
  `git grep -n -w 'Chr''is'` exits 1. (The quotes split the words so this plan does not match
  itself.)
- **AC7. The commit identity holds.** `git log --format='%ae%n%ce' | sort -u > /tmp/kit-001-ids.txt`,
  then `cat /tmp/kit-001-ids.txt` prints only `hello@glosswork.dev`.
- **AC8. AGENTS.md carries the three traps and the command, with a version.**
  `grep -n 'env -i' AGENTS.md`, `grep -n 'CLAUDE_CONFIG_DIR="$(mktemp -d)"' AGENTS.md`,
  `grep -n 'docs/changes/' AGENTS.md`, `grep -n -i 'terminal' AGENTS.md` and
  `grep -n 'user_config.address' AGENTS.md` each exit 0, and each new trap's text names a
  Claude Code version (read by the verifier, the one criterion that is a reading).
- **AC9. CONTRIBUTING says what the gate is.** `grep -n gitleaks CONTRIBUTING.md` exits 0.
- **AC10. Secret detection fails on a finding (mutation, never pushed).** In a scratch clone
  of the branch with its remote removed, commit a file holding a randomly generated string in
  GitHub's personal-token shape, then run
  `gitleaks git . --redact --no-banner --exit-code 1` with gitleaks 8.30.1: exits 1 with one
  finding. The same command on the branch itself exits 0. Delete the scratch clone.
- **AC11. The validate fence.** `env -i PATH="$PATH" HOME="$(mktemp -d)" CLAUDE_CONFIG_DIR="$(mktemp -d)" claude plugin validate . --strict`
  exits 0, with the Claude Code version printed by `claude --version` recorded. A fence: this
  change does not touch the manifests.
- **AC12. The warning test can fail.** The two mutations of checklist step 6, re-run by the
  verifier: each makes
  `uv run --frozen pytest -q tests/test_mcpb_manifest.py -k readme` exit 1.
- **AC13. The manifest identity test can fail.** The mutation of checklist step 7, re-run by
  the verifier: `GLOSSWORK_HARNESS=1 uv run --frozen pytest -q -m harness -k manifest`
  exits 1, and exits 0 once the byte is restored and the bundle rebuilt.
- **AC14. GitHub's own scanning is on.** The maintainer's result from checklist step 13,
  quoted. Not provable by an agent's token.
- **AC15. After closeout.** `uv run --frozen pytest -q` exits 0 with no deselection, and
  `ls docs/changes` prints only `README.md`.

## Adversarial pass

## Deviations from the approved plan

## Durable content moved out of this plan
