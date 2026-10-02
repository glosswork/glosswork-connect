# 001: the public kit says what is true, ships no build files, and its tests guard what they claim to

| | |
| --- | --- |
| Issue | #1 (to be filed after plan approval) |
| Branch | `1-public-kit-cleanup` |
| Depends on | Nothing to merge first. Before any step that runs the image: `docker.io/glosswork/glosswork:latest` is published (checklist step 0) |

This is GitHub change 1. It is not "archive 001", which was numbered by the private archive
(see `docs/changes/README.md`). Issue and pull request numbers share one sequence on GitHub,
and on 2026-10-02 the repository had no issue and no pull request, so the next number is 1.
If anything else takes number 1 before this issue is filed, the branch and this file are
renamed to the number the issue actually gets, before anything is pushed.

## Why

The repository became public on 2026-10-02. A stranger who reads it today finds text that
was true while it was private and is not now, a personal image name, a person's first name
where the maintainer is meant, internal decision and task numbers in test docstrings and
fixture names, instructions that disagree with how the plugin is actually installed, a
Claude Desktop extension that ships its own build script, and two tests that guard less than
their names say. None of it is a leaked credential, and none of it stops the kit from
working. All of it is what a careful reader judges the kit by.

The changes are small and touch the same few files, so they go in one change rather than
several, each of which would carry a full plan, review and pull request of its own.

## Premises

Every premise below was established on 2026-10-02 in a fresh clone of
`https://github.com/glosswork/glosswork-connect` at `12a23ad` (the only commit), on macOS
(arm64) with uv 0.9.18, Node 22.17.1, npm 10.9.2, Docker 28.4.0, gitleaks 8.30.1 and Claude
Code 2.1.287 (the current npm release, `npm view @anthropic-ai/claude-code version`, read
2026-10-02). Every Claude Code command ran under `env -i` with a scratch `HOME` and a scratch
`CLAUDE_CONFIG_DIR`. Nothing in a real Claude Code configuration was read or written. The
adversarial pass re-ran P2, P3, P4, P6, P7, P13 (the CI and branch reads), P15, P16, P17 and
P20 the same day in its own fresh clone, with Claude Code 2.1.287 in a `node:22-bookworm`
container, and each held except where a premise below says otherwise.

**P1. The README says things that stopped being true when the repository went public.**
Read in `README.md`: lines 7 to 8 say the repository "is private until the site is live" and
that installs come "from a local clone or from a file sent to them"; line 14 says the
marketplace is "added from a local clone"; line 37 tells the reader to run
`claude plugin marketplace add <path to a clone of this repository>`; line 17 says the
extension is "not yet installed in Claude Desktop" and lines 65 to 68 that it "has not been
installed in Claude Desktop yet". `.github/ISSUE_TEMPLATE/bug.md` line 19 asks whether the
install came from "a local clone, or a file that was sent". The Claude Desktop install was
made by the maintainer on 2026-10-02; that is the maintainer's statement, not a measurement
this change made. The README does not name a Claude Desktop version.

**P2. The marketplace installs from GitHub by its short name, and that install copies only
the repository's files.** Measured: `claude plugin marketplace add glosswork/glosswork-connect`
exits 0 ("cloning via HTTPS"), `claude plugin install glosswork@glosswork --scope user` exits
0 and reports the two unset values. The plugin's copy in the scratch configuration directory
holds 36 files, which is exactly `git ls-files | wc -l` (36); `du` gives 244 KB on macOS and
304 KB on Linux, a block-size difference. No `.venv`, `.pytest_cache`, `.ruff_cache` or
`.git`.

**P3. Added from a working clone, the marketplace copies the whole directory, untracked files
included.** Measured: in a clone where `uv sync --frozen` and `uv run pytest -q` had run, the
same two commands with the clone's path copied the whole directory into
`plugins/cache/glosswork/glosswork/0.2.0/` of the scratch configuration directory: 702 files
and 31 MB in one clone, 694 files and 32 MB in another, including `.venv`, `.pytest_cache`
and `.ruff_cache`, all three of which `.gitignore` names. Only `.git` was left out. So any
untracked file in a clone, a stray token file included, would be copied into the person's
Claude Code configuration directory. Nothing in the kit can make a local directory install
skip files, so the fix is to tell people to add the marketplace from GitHub, to say why, and
to say that a local directory install should be a fresh clone with nothing untracked in it.

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

**P5. A project setting removes that line without changing the plugin.** Measured in the
same Linux container setup as P4, Claude Code 2.1.287: with a `.claude/settings.json` at the
clone root holding `{"disabledMcpjsonServers": ["glosswork"]}`, `claude mcp list` from the
clone root lists only `plugin:glosswork:glosswork`, and `claude mcp get glosswork` reports the
project server as "Rejected (see disabledMcpjsonServers in settings)". The plugin's own server
is still listed and still attempts its connection. `claude plugin validate . --strict` exits
0 with the file present. Installed from a local clone that carries the file, the plugin's
server is still listed from an unrelated directory. Not measured: a real connection with the
file present, which this setting cannot reach because it names only the project server.

**P6. `claude plugin validate` writes into the Claude Code configuration directory.**
Measured: `claude plugin validate . --strict` under `env -i` with a scratch
`CLAUDE_CONFIG_DIR` exits 0 ("Validation passed") and leaves a `.claude.json` and a
`backups` directory in that directory. Run without a scratch directory, it would write to the
person's own Claude Code configuration. `AGENTS.md` line 22 gives the command bare.

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
With only the image constant changed to the public release image, the same command exits 0:
16 passed. That run used the one tag Docker Hub published on 2026-10-02, because the tag this
change names, `docker.io/glosswork/glosswork:latest`, did not exist yet
(`docker manifest inspect docker.io/glosswork/glosswork:latest` exits 1, read 2026-10-02). So
the harness has not yet been run against `:latest`, and the build runs it there (checklist
steps 0 and 1). The name also stays in the history of commit `12a23ad`; this change removes
it from the tree only.

**P10a. Test text names internal decision and task numbers that mean nothing to a reader.**
Read: six docstrings and comments cite an internal decision number
(`tests/test_mcpb_manifest.py` lines 32, 98, 181 and 189, `tests/test_mcpb_bundle.py` lines
581 and 592); `tests/test_mcpb_manifest.py` line 133 cites an internal design-question
number; and eleven harness names (container, volume, scratch directories, tokens, admin
address, client) are built on an internal task number (`tests/test_mcpb_bundle.py` lines 44,
45, 108, 164, 176, 231, 232, 341, 642 and 685, and `tests/support/stub_oauth.mjs` line 77). None is a secret. Each is a reference a stranger
cannot follow.

**P11. CONTRIBUTING names a person where it means the maintainer.** Read at `CONTRIBUTING.md`
lines 12, 48 and 58. `LICENSE` already names the company, Heavylift Labs LLC, and the three
manifests name Heavylift Labs as author.

**P12. The commit identity rule already holds, and CI enforces it.** Measured:
`git log --format='%ae%n%ce' | sort -u` prints only `hello@glosswork.dev`. Read at
`.github/workflows/ci.yml` lines 81 to 87: the `secrets` job fails on any commit whose author
or committer is not `hello@glosswork.dev` or GitHub's own web-merge committer. This change
keeps it true by committing as `hello@glosswork.dev` (set in this clone's local config). Read
through the repository endpoint: merge commits, squash merges and rebase merges are all
allowed, so the merge method and the email chosen at merge time are the maintainer's to get
right (see Constraints).

**P13. Secret detection already fails CI on a finding.** Read at `ci.yml` lines 66 to 80: the
`secrets` job downloads gitleaks 8.30.1, checks it against a SHA-256 that matches the
published `gitleaks_8.30.1_checksums.txt` entry for `linux_x64` (verified 2026-10-02), and
runs `gitleaks git . --redact --no-banner --exit-code 1` with `fetch-depth: 0`, which with no
`--log-opts` scans every commit on every branch the checkout fetched, not only the pull
request's. No step or job sets `continue-on-error`, so a failing step fails the job.
Mutation, in a scratch clone whose remote was removed and which was never pushed: the same
gitleaks command on the clean history exits 0 ("no leaks found"); after committing one file
holding a randomly generated string in GitHub's personal-token shape, it exits 1 with one
finding, rule `github-pat`, secret redacted; `tests/test_no_credentials.py` also fails on it
(1 failed, 3 passed). The last CI run on `main` (`12a23ad`, run 36285380840, a push) passed
`lint`, `test` and `secrets`; no pull request has run CI here yet. Read through the API's
branch endpoint: `main` is protected, with required checks `lint`, `test` and `secrets` and
enforcement level `everyone`, and the repository has no rulesets. That endpoint does not show
whether a pull request is required, or whether force pushes and deletion are blocked. What is
missing is that CONTRIBUTING does not say what the `secrets` check does.

**P14. The workflow's comment about GitHub's own scanning is out of date.** Read at `ci.yml`
lines 58 to 61: GitHub secret scanning "is not available to a private repository on this plan
without a paid add-on, so this is the scanner until the repository is public". Whether GitHub
secret scanning and push protection are now on is not readable with a non-admin token
(`security_and_analysis` reads null, the alerts endpoint 404, and the token reports
`admin: false`). GitHub's documentation (read 2026-10-02) puts both under Settings, then
Advanced Security in the "Security and quality" part of the sidebar, then Secret Protection,
and push protection can be enabled only once Secret Protection is.

**P15. The Claude Desktop bundle ships its build script and its README.** Measured: after
`bash mcpb/build.sh` (mcpb 2.1.2), the bundle holds 729 files; outside `node_modules/` they
are `README.md`, `build.sh`, `manifest.json` and `package.json`. `mcpb/package-lock.json` is
already left out by the packer; npm's own `node_modules/.package-lock.json` ships.

**P16. An unanchored ignore pattern strips files the proxy's dependencies carry.** Measured
in a scratch build: an `mcpb/.mcpbignore` of `build.sh`, `README.md`, `package-lock.json`
shrinks the bundle to 645 files, because `README.md` matches case-insensitively at any depth:
it removes the root `README.md` and 82 readme files inside `node_modules/` (63 `README.md`,
12 `readme.md`, 8 `Readme.md`), plus `build.sh`. Anchored as `/build.sh`, `/README.md`,
`/package-lock.json`, the bundle holds 727 files: exactly the 729 minus the root `README.md`
and `build.sh`, `node_modules/mcp-remote/README.md` still present, and the `.mcpbignore` file
itself not shipped. With the anchored file and the public release image, the full harness
suite passes (16 passed, exit 0).

**P17. The packer does not rewrite the manifest.** Measured: `cmp` of the `manifest.json`
inside the built bundle with `mcpb/manifest.json` exits 0, with and without the ignore file,
both when read with `unzip` and when unpacked with `mcpb unpack` as the harness fixture does.
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
     the repository's files; anyone who must add it from a local directory uses a fresh
     clone with nothing untracked in it.
   - Line 29: "paste the address, then paste the token as an `Authorization` header" and
     nothing about a second header. The label rides on the token, as line 60 already says.
   - Lines 17 and 65 to 68: the "not yet installed" and "has not been installed" statements
     are replaced by plain text that agrees with the install page: build the bundle, open it,
     and Claude Desktop installs it and asks for the two values. No Claude Desktop version is
     named. The harness measurements of 2026-09-18 stay credited to the harness tests. Line
     17 keeps its clear-text warning.
   - The Claude Code connection claims that were measured on 2.1.274 (Keychain storage, the
     masked field, survival across restart) keep their 2.1.274 label. This change re-measures
     only the install path and a connection on Linux (checklist step 10), and the README
     says exactly that and no more.
   - The bundle paragraph says `mcpb/.mcpbignore` keeps the build script and the README out
     of the bundle.
   - The Connecting Claude Desktop section says the harness tests run against
     `docker.io/glosswork/glosswork:latest`, a tag that moves, so a result names the image
     digest it ran against rather than the tag.

2. **`.github/ISSUE_TEMPLATE/bug.md` line 19** asks where the install came from: the GitHub
   marketplace, a clone (fresh or not), or a `.mcpb` built from which commit.

3. **`pyproject.toml` line 37 and `tests/test_mcpb_bundle.py` lines 6 and 43** name
   `docker.io/glosswork/glosswork:latest`, by the maintainer's decision of 2026-10-02 that
   the kit refers to the image by `:latest` and never by a version. The tradeoff, stated
   plainly: a floating tag means a harness run today and one next month may use different
   images, so a harness failure may be an image change rather than a kit change. Each
   harness run in this change pulls the tag first and records the digest it ran against.

4. **`CONTRIBUTING.md`.** Line 12: "**Maintainer** means Heavylift Labs, which publishes
   Glosswork." Lines 48 and 58: "the maintainer merges". The "Branches and commits" section
   gains what the `secrets` check is: gitleaks 8.30.1, checksum-verified, over every commit
   on every branch the CI checkout fetched, failing on any finding, plus the commit identity
   check; and, once the maintainer has confirmed them (step 13), that GitHub secret scanning
   and push protection are on for the repository. It also says a web merge uses "Create a
   merge commit" with `hello@glosswork.dev` chosen as the commit email.

5. **`.github/workflows/ci.yml` lines 55 to 61.** The comment stops saying GitHub scanning is
   unavailable until the repository is public. It says gitleaks in CI is the gate a pull
   request cannot pass without, and that GitHub's own secret scanning and push protection
   are repository settings, described in CONTRIBUTING. No step changes.

6. **`AGENTS.md` and `.claude/settings.json`.**
   - Commands: the validate row becomes
     `env -i PATH="$PATH" HOME="$(mktemp -d)" CLAUDE_CONFIG_DIR="$(mktemp -d)" claude plugin validate . --strict`,
     with one sentence on why (P6), naming the Claude Code version.
   - Traps, new entries, each naming the Claude Code version measured:
     (a) a raw terminal capture of Claude Code's screen cannot prove what it showed, so a
     screen is rendered through a terminal emulator before anyone reads it (P8, re-measured
     in step 9);
     (b) Claude Code copies the whole plugin directory, `docs/changes/` included, into the
     configuration directory, so no file in this repository writes the token prefix whole
     (P7);
     (c) a Claude Code session started in a clone of this repository would see the plugin's
     `.mcp.json` as a project server with a literal `${user_config.address}`, which is why
     `.claude/settings.json` exists; do not remove it (P5).
   - Harness wording: line 32's "they never touch a pilot's" becomes "they never touch a real
     workspace".
   - **`.claude/settings.json`** (new), holding `{"disabledMcpjsonServers": ["glosswork"]}`
     (P5), decided by the maintainer on 2026-10-02. With it, a Claude Code session in a clone
     does not offer the plugin's server a second time, and `claude mcp list` from the clone
     root lists no `glosswork` server other than `plugin:glosswork:glosswork`, while the
     plugin, its manifests and its tests stay as they are. Its cost is one tracked file that
     every contributor's Claude Code session in a clone obeys.

7. **`mcpb/.mcpbignore`** (new): `/build.sh`, `/README.md` and `/package-lock.json`, each
   anchored to the bundle root (P16). The last is already excluded by the packer and is
   listed so the intent survives a packer change.

8. **Tests.** Each new or rewritten test carries the name given here, because the Accept
   block selects tests by name.
   - `tests/test_mcpb_manifest.py`, `test_the_readme_warns_that_a_network_address_sends_the_token_in_clear_text`
     (rewritten in place): each file's text, with whitespace collapsed, must contain its
     exact warning sentence: in `README.md`, "A plain `http://` address that is not on this
     machine sends the token across the network in clear text."; in `mcpb/README.md`, the
     heading "A plain HTTP address on your network sends the token in clear text". The
     three-word check is retired for the two READMEs and kept for the manifest's address
     description, which has its own test and is not in scope.
   - `tests/test_mcpb_manifest.py`, `test_the_bundle_ignore_file_anchors_each_pattern_to_the_bundle_root`:
     `mcpb/.mcpbignore` exists, and its lines, ignoring blank lines and `#` comments, are
     exactly the three anchored patterns.
   - `tests/test_mcpb_bundle.py` (harness), `test_the_bundle_root_holds_only_the_manifest_and_package_json`:
     read from the zip listing of `mcpb/dist/glosswork.mcpb`, the entries with no `/` are
     exactly `manifest.json` and `package.json`, and `node_modules/mcp-remote/README.md` is
     present (the guard against an unanchored pattern).
   - `tests/test_mcpb_bundle.py` (harness), `test_the_bundled_manifest_is_the_source_manifest`:
     the `manifest.json` inside the built bundle is byte-identical to `mcpb/manifest.json`.
   - `tests/test_license_and_readme.py`, `test_the_readme_installs_from_github_and_says_nothing_stale`:
     the README, with whitespace collapsed, names
     `claude plugin marketplace add glosswork/glosswork-connect`, and does not contain
     `<path to a clone`, "second header", "private until", "a file sent", "not yet installed
     in Claude Desktop" or "installed in Claude Desktop yet".
   - `tests/test_layout.py`, `test_the_clone_does_not_offer_the_plugins_server_as_a_project_server`:
     `.claude/settings.json` parses, and its `disabledMcpjsonServers` is exactly the list of
     keys of `.mcp.json`'s `mcpServers`.
   - The internal references of P10a go: the docstrings and comments say the plain reason
     (the accepted cost of reaching a workspace on the person's own network, and the
     platform answer), and every harness name built on the internal task number becomes
     `kit-harness` (container `kit-harness-gw`, volume `kit-harness-data`, and so on, the
     admin address `kit-harness@example.invalid`), in `tests/test_mcpb_bundle.py`,
     `tests/test_mcpb_manifest.py` and `tests/support/stub_oauth.mjs`.

## What does not change

- No behavior of the plugin, `.mcp.json`, `.claude-plugin/`, `mcpb/manifest.json`,
  `mcpb/package.json`, `mcpb/build.sh`, the skills, or the guidance hashes. So
  `claude plugin validate` is run as a local fence, not as evidence of a change. The new
  `.claude/settings.json` is not a plugin file; validate is run with it present.
- The CI jobs and their ids (`lint`, `test`, `secrets`), their steps and the pinned gitleaks
  version and checksum. Only a comment in `ci.yml` changes.
- The README statements measured on Claude Code 2.1.274 keep that version.
- The history. Commit `12a23ad` keeps the personal image name and the first name it already
  carries; removing them from history would mean rewriting a public `main`, which is outside
  this change and is the maintainer's call.
- Text deliberately left: `docs/changes/README.md`'s note on the private archive, the
  README's "kept in a private archive" line, and the generic word "pilot" for an early user
  in the Change template and one test docstring, none of which names anyone.
- No new test scans for the personal names or the internal numbers, because a public test
  would have to spell them. The Accept block checks them with `git grep` instead.

## Constraints

- Every commit is authored and committed as `Glosswork <hello@glosswork.dev>`, with no
  session or co-author trailer.
- Nothing is pushed until the closeout, once. No issue, pull request or comment is posted on
  GitHub before the maintainer approves its wording.
- No GitHub setting is changed by an agent. Step 13 is the maintainer's.
- The maintainer merges in the web page with "Create a merge commit" and chooses
  `hello@glosswork.dev` as the commit email, never squash or rebase, so the merge commit is
  authored as `hello@glosswork.dev` and committed by GitHub (AC16).
- No file writes the access token's prefix whole, including this plan.
- Claude Code commands run under `env -i` with a scratch `HOME` and `CLAUDE_CONFIG_DIR`. Any
  step that stores a token runs in a Linux container, so no macOS keychain item is written.
- The image is `docker.io/glosswork/glosswork:latest` everywhere, and nothing falls back to
  a versioned tag. Every step that runs the image is preceded by checklist step 0, and does
  not start until it holds. Each harness run pulls the tag first and records
  `docker image inspect --format '{{index .RepoDigests 0}}' docker.io/glosswork/glosswork:latest`.
- Harness runs use a scratch workspace from that image, which the tests start and remove.
  They never point at a real workspace.
- `mcpb/dist/` is deleted before every harness run in this change, because the bundle fixture
  reuses an existing bundle.
- README text a stranger reads stays plain and claims nothing the kit has not measured. No em
  dashes.
- The full suite's exit code is read with `test_the_change_plan_directory_holds_only_its_readme`
  deselected until the closeout deletes this file, and in full after it (P19).

## Checklist

0. **Precondition for every step that runs the image (1, 2, 7, 8, 10 and Accept AC3, AC4,
   AC13).** `docker manifest inspect docker.io/glosswork/glosswork:latest > /dev/null` exits
   0, then `docker pull docker.io/glosswork/glosswork:latest` exits 0 and its digest is
   recorded. If the manifest inspect exits 1, those steps wait, the build records that it is
   waiting, and nothing falls back to a versioned tag. Steps that do not run the image may
   go ahead in order.
1. Write the new and changed assertions of "What changes" item 8, and the image constant
   only, then run them against the otherwise unchanged tree and record how each fails:
   - `uv run pytest -q tests/test_license_and_readme.py`: fails on the marketplace command,
     the clone path and the stale phrases.
   - `uv run pytest -q tests/test_mcpb_manifest.py`: the `.mcpbignore` test fails (no file).
     The rewritten warning test passes on `main`, which is expected; its proof is the
     mutation in step 6.
   - `uv run pytest -q tests/test_layout.py -k project_server` fails (no
     `.claude/settings.json`).
   - `rm -rf mcpb/dist && GLOSSWORK_HARNESS=1 uv run pytest -q -m harness`: the bundle
     root-entries test fails naming `README.md` and `build.sh`; the manifest identity test
     passes (P17), and its proof is the mutation in step 7.
2. Add `mcpb/.mcpbignore`. Rerun step 1's harness command: all pass.
3. Change `pyproject.toml` line 37 to the `:latest` image, and replace the internal
   references of P10a.
4. Edit `README.md` and `bug.md` as in items 1 and 2. Rerun `tests/test_license_and_readme.py`:
   passes.
5. Edit `CONTRIBUTING.md` and the `ci.yml` comment as in items 4 and 5 (the secret-scanning
   sentence waits for step 13).
6. Mutation for the warning test, in a scratch copy: delete `README.md`'s warning paragraph;
   the new test fails and the old one, run from `main`, passes. Then replace the sentence with
   a rewording that keeps "network" and "token"; the new test fails. Then reword the
   `mcpb/README.md` heading, keeping "network" and "token"; the new test fails. Record all
   three.
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
    install, configure against a scratch workspace from the `:latest` image with a scratch
    token, and record `claude mcp list` showing the plugin's server connected, and the image
    digest. The README status for line 14 names that Claude Code version.
11. Re-measure P2, P3, P4 and P5 on the then-current Claude Code if it is
    newer than 2.1.287, and write the version measured into the README paragraph and the
    AGENTS.md traps.
12. Edit `AGENTS.md` and add `.claude/settings.json`, as in item 6.
13. **The maintainer**, in the GitHub web page. Settings, then Advanced Security (sidebar,
    "Security and quality"): next to Secret Protection click Enable and confirm with "Enable
    Secret Protection"; then, in the Secret Protection section, click Enable next to Push
    protection. Then Settings, Branches, the rule for `main`: confirm it requires a pull
    request, requires `lint`, `test` and `secrets`, applies to administrators, and blocks
    force pushes and deletion. The maintainer records what each page shows in writing, and
    the pull request quotes it. An agent's token cannot read either page; the branch
    endpoint's partial read (P13) is supporting evidence, not the confirmation. The result
    goes into CONTRIBUTING as item 4 says, and anything not on goes in Deviations.
14. Run the Accept block.

## Accept

Run from the repository root on the branch, with `UV_NO_CONFIG=1` exported. Each exit code is
read on its own, never through a pipe. AC3, AC4 and AC13 need checklist step 0 to hold.

- **AC1. Lint, two commands.** `uv run --frozen ruff check .` exits 0, then
  `uv run --frozen ruff format --check .` exits 0.
- **AC2. The structural suite.**
  `uv run --frozen pytest -q -rA --deselect tests/test_layout.py::test_the_change_plan_directory_holds_only_its_readme`
  exits 0, and its passed list names each new structural test of item 8.
- **AC3. The harness suite, against `:latest`.**
  `docker manifest inspect docker.io/glosswork/glosswork:latest >/dev/null` exits 0,
  `docker pull docker.io/glosswork/glosswork:latest` exits 0 and the digest is recorded, then
  `rm -rf mcpb/dist && GLOSSWORK_HARNESS=1 uv run --frozen pytest -q -m harness` exits 0 with
  no skips.
- **AC4. The bundle ships no build files.** After AC3,
  `unzip -Z1 mcpb/dist/glosswork.mcpb > /tmp/kit-001-bundle.txt` exits 0, then
  `grep -c -v / /tmp/kit-001-bundle.txt` prints `2`, and
  `grep -x -e build.sh -e README.md -e package-lock.json -e .mcpbignore /tmp/kit-001-bundle.txt`
  exits 1, and `grep -x node_modules/mcp-remote/README.md /tmp/kit-001-bundle.txt` exits 0.
- **AC5. The stale text is gone.** Each of these exits 1:
  `grep -n "second header" README.md`;
  `grep -n -i "private until" README.md`;
  `grep -n "path to a clone" README.md`;
  `grep -n -i "file sent" README.md`;
  `grep -n -i "not yet installed" README.md`;
  `grep -n -i "installed in Claude Desktop yet" README.md`;
  `grep -n "repository is public" .github/workflows/ci.yml`;
  `grep -n "paid add-on" .github/workflows/ci.yml`.
  And `grep -n "claude plugin marketplace add glosswork/glosswork-connect" README.md` exits 0.
  (The ci.yml phrase is split across two lines on `main`, so the first draft's
  "until the repository is public" exited 1 before any change and proved nothing.)
- **AC6. No personal identifier or internal number in the tree.** Each exits 1:
  `git grep -n -i 'csch''eide'`, `git grep -n -w 'Chr''is'`,
  `git grep -n -i 'con''n05'`, `git grep -n -w -e 'Q''51' -e 'D''4'`. And
  `git grep -n 'glosswork/glosswork:latest' pyproject.toml tests/test_mcpb_bundle.py` exits 0.
  (The quotes split the words so this plan does not match itself.)
- **AC7. The commit identity holds.** `git log --format='%ae%n%ce' > /tmp/kit-001-ids.txt`
  exits 0, then `grep -v -x hello@glosswork.dev /tmp/kit-001-ids.txt` exits 1.
- **AC8. AGENTS.md carries the traps and the command, with a version.** Each exits 0:
  `grep -n 'env -i' AGENTS.md`, `grep -n 'CLAUDE_CONFIG_DIR="$(mktemp -d)"' AGENTS.md`,
  `grep -n -i 'token prefix' AGENTS.md`, `grep -n -i 'terminal emulator' AGENTS.md` and
  `grep -n 'user_config.address' AGENTS.md`; each of these exits 1 on `main`. Each new trap's
  text names a Claude Code version (read by the verifier, the one criterion that is a
  reading). (`docs/changes/` is not a criterion: `AGENTS.md` names it on `main` already.)
- **AC9. CONTRIBUTING says what the gate is.** `grep -n gitleaks CONTRIBUTING.md` exits 0.
- **AC10. Secret detection fails on a finding (mutation, never pushed).** In a scratch clone
  of the branch with its remote removed, commit a file holding a randomly generated string in
  GitHub's personal-token shape, then run
  `gitleaks git . --redact --no-banner --exit-code 1` with gitleaks 8.30.1: exits 1 with one
  finding. The same command on the branch itself exits 0. Delete the scratch clone.
- **AC11. The validate fence.** `env -i PATH="$PATH" HOME="$(mktemp -d)" CLAUDE_CONFIG_DIR="$(mktemp -d)" claude plugin validate . --strict`
  exits 0, with the Claude Code version printed by `claude --version` recorded. A fence: this
  change does not touch the manifests.
- **AC12. The warning test can fail.** The three mutations of checklist step 6, re-run by the
  verifier: each makes
  `uv run --frozen pytest -q tests/test_mcpb_manifest.py -k readme` exit 1.
- **AC13. The manifest identity test can fail.** The mutation of checklist step 7, re-run by
  the verifier: `GLOSSWORK_HARNESS=1 uv run --frozen pytest -q -m harness -k bundled_manifest`
  exits 1, and exits 0 once the byte is restored and the bundle rebuilt.
- **AC14. GitHub's own scanning and branch protection are on.** The maintainer's written
  result from checklist step 13, quoted. Not provable by an agent's token.
- **AC15. After closeout.** `uv run --frozen pytest -q` exits 0 with no deselection, and
  `ls docs/changes` prints only `README.md`.
- **AC16. After the merge.** On a fresh fetch of `main`,
  `git log origin/main --format='%ae%n%ce' > /tmp/kit-001-main-ids.txt` exits 0, then
  `grep -v -x -e hello@glosswork.dev -e noreply@github.com /tmp/kit-001-main-ids.txt`
  exits 1, and the CI run on the merge commit shows `lint`, `test` and `secrets` succeeded.
- **AC17. No project server inside a clone.** In a Linux container with
  the then-current Claude Code, the plugin installed from the branch and configured with a
  placeholder, `claude mcp list` run from the clone root prints no line starting
  `glosswork:`, with the Claude Code version recorded.

## Adversarial pass

Run on 2026-10-02 by a session that did not write the plan, in its own fresh clone of
`main` at `12a23ad` and in `node:22-bookworm` containers with Claude Code 2.1.287. Every fix
accepted below is folded into the text above.

- **F1. The image is named by `:latest`, not by a version.** The maintainer decided on
  2026-10-02 that every reference to the image uses `:latest`. That tag did not exist that
  day (`docker manifest inspect docker.io/glosswork/glosswork:latest` exits 1; only one
  versioned tag was published). *Accepted, from the maintainer.* Items 1 and 3, P10,
  Constraints, checklist step 0 and AC3 now name `:latest`, every image step waits for it,
  nothing falls back to a version, and each harness run records the digest it ran against,
  because a floating tag can change between runs.
- **F2. AC5's `ci.yml` check could not fail.** "until the repository is public" is split
  across lines 59 and 60 on `main`, so the grep exits 1 before any change. *Accepted.* AC5
  greps "repository is public" and "paid add-on", both present on `main` today.
- **F3. AC8's `docs/changes/` check could not fail.** `AGENTS.md` names `docs/changes/` in
  "Where things are" on `main`. *Accepted.* AC8 greps "token prefix" and "terminal emulator"
  instead, each absent on `main`.
- **F4. The stale Desktop line in the table was unguarded.** README line 17 says "not yet
  installed in Claude Desktop", which neither the new test's phrase nor AC5 matched, and
  "a file sent" (lines 7 to 8) was not checked at all. A phrase broken across lines would
  also slip past a line-based check. *Accepted.* The README test collapses whitespace and
  checks both Desktop phrasings and "a file sent"; AC5 greps them.
- **F5. A cheaper way to stop the duplicate server inside a clone.** A tracked
  `.claude/settings.json` with `disabledMcpjsonServers` removes the duplicate server from
  `claude mcp list` inside a clone, leaves the plugin's own server listed, and passes
  `validate --strict` (P5). It meets the requirement's stronger form without touching the
  plugin. *Accepted, decided by the maintainer* on 2026-10-02 and folded into item 6. The
  alternatives, a warning in AGENTS.md only or moving the server into the plugin manifest,
  were set aside.
- **F6. The fresh-clone half of the install requirement.** Pointing the README at GitHub
  solves the problem, but the requirement also allows "install from a fresh clone and say
  why", and someone without GitHub access still uses a local directory. *Accepted.* The
  README paragraph says a local install must be a fresh clone with nothing untracked.
- **F7. Branch protection was asserted from a partial read.** The branch endpoint shows the
  three required checks and `everyone`, and there are no rulesets, but it does not show
  whether a pull request is required, or whether force pushes and deletion are blocked, and
  the requirement asks the maintainer to confirm branch protection. *Accepted.* Step 13 has
  the maintainer confirm the branch rule as well, in writing, and AC14 quotes it.
- **F8. The merge could put a personal identity on public `main`.** Merge, squash and rebase
  are all enabled, and a web merge takes the email the maintainer picks. A personal address
  in the merge commit fails the `main` run's identity check and stays in public history.
  *Accepted.* Constraints and CONTRIBUTING say "Create a merge commit" with
  `hello@glosswork.dev`, and AC16 checks `main` after the merge.
- **F9. The `secrets` scope was described too narrowly.** With `fetch-depth: 0` and no
  `--log-opts`, gitleaks and the identity check read every fetched branch, not the pull
  request's commits, so one bad branch on GitHub turns every pull request red. *Accepted for
  the wording* (P13, item 4). *Deferred to the maintainer for the behavior*: narrowing the
  scan is a CI change, outside this change. No pull request has run CI here yet, so how the
  identity check treats the merge GitHub builds for a pull request run is not established;
  the closeout reads the `secrets` job of the first run.
- **F10. Internal decision and task numbers in public test text.** Seven docstrings and
  comments cite internal decision numbers, and eleven harness names are built on an
  internal task number (P10a). *Accepted.* Item 8 replaces them, and AC6 checks them.
- **F11. The title overclaimed.** "Ships only what it runs" is not true after this change:
  the bundle still carries dependency READMEs and licenses. *Accepted.* The title and AC4
  say "ships no build files". The issue draft's title changes to match.
- **F12. P16 miscounted.** The unanchored pattern removes 82 readme files inside
  `node_modules/` plus the root `README.md`, not 83 inside `node_modules/`; the totals (729,
  645, 727) reproduce. *Accepted*, corrected in P16.
- **F13. The Accept selectors depended on unnamed tests.** AC12 selects `-k readme` and AC13
  `-k manifest`, which would also catch the root-entries test. *Accepted.* Item 8 names
  every test, AC13 selects `bundled_manifest`, the root-entries test reads the zip listing
  rather than the unpacked directory, and the ignore-file test skips blank lines.
- **F14. The `mcpb/README.md` half of the warning test had no mutation.** *Accepted.* Step 6
  and AC12 reword its heading too.
- **F15. The maintainer's GitHub steps.** The documented path names the "Security and
  quality" sidebar group and an "Enable Secret Protection" confirmation, and push
  protection needs Secret Protection first. The suggested `gh api` check needs an admin
  token, and the token in use reports `admin: false`. *Accepted.* Step 13 gives the exact
  path and has the maintainer record what the pages show.
- **F16. AC7 was a reading.** *Accepted.* It is a `grep -v -x` that must exit 1.
- **F17. The plan file's own failure (P19).** Checked: the full suite fails only on
  `test_the_change_plan_directory_holds_only_its_readme` while this file exists, AC2
  deselects exactly that test, and AC15 runs the full suite after the closeout deletes the
  file, before the one push. *No change.* The plan's commits stay in the branch history a
  merge commit keeps, so this file's wording is public for good, which F10 and F11 account
  for.

## Deviations from the approved plan

The build ran on 2026-10-02. Every image step ran against
`docker.io/glosswork/glosswork:latest` at digest
`sha256:66b88b181b3012f92e3a51854237ab3327a5c4b7480c3191c8409529ae33a82d`, pulled before each
run (steps 0, 1, 2, 7, 8 and 10). Claude Code on npm was 2.1.288 that day, newer than the
2.1.287 the premises name, so step 11 applied.

- **Deviation 1. Claude Code 2.1.288, not 2.1.287.** Steps 9, 10 and 11 ran on 2.1.288 in
  `node:22-bookworm` containers, and the README and AGENTS.md name 2.1.288. P2, P3, P4 and P5
  held on it: the GitHub install copies 36 files; a used clone added as a directory copies
  695 files and 32 MB, `.venv`, `.pytest_cache` and `.ruff_cache` included; the duplicate
  project server appears from a clone root and not from `/`; with `.claude/settings.json`
  it is gone, `claude mcp get glosswork` reports it "Rejected", and validate exits 0. The
  premises above keep the version they were measured on.
- **Deviation 2. P6 was re-measured too.** Step 11 names P2 to P5 only. Because the AGENTS.md command
  row names a version, P6 was also run on 2.1.288 (macOS, `env -i`, scratch directories):
  validate exits 0 and leaves `.claude.json` and `backups` in the configuration directory.
- **Deviation 3. The README named 2.1.288 at step 4, before step 10 measured it.** The version was
  read from npm at step 4 and written then; steps 10 and 11 then measured the install, the
  connection and the copy behaviour on that version, and all held, so the text stands.
- **Deviation 4. Step 1's README test stops at its first assertion.** On the unfixed tree it failed
  on the marketplace command, so the stale phrases were checked separately with the test's
  own `STALE_README_PHRASES`: all six were present.
- **Deviation 5. Step 9's capture tool.** The raw capture was taken with Python's `pty` module and
  rendered with `pyte` 0.8.2, a terminal emulator library, rather than with `script`, which
  hung for the plan run. On the rendered first screen "Let's get started." is a line; the
  raw bytes hold it as `Let's`, a cursor move, `get`, a cursor move, `started.`, and
  `grep -c -F` for the whole line in the raw capture prints 0.
- **Deviation 6. "Pilot" in test text.** "What does not change" keeps the generic word in one test
  docstring; there are two, in `tests/test_mcpb_manifest.py` (the compatibility block test)
  and `tests/test_mcpb_bundle.py` (the scratch workspace fixture). No item of "What changes"
  names either, so both stay as they were.
- **Deviation 7. Step 13 has not happened yet.** It is the maintainer's. Until it does,
  CONTRIBUTING carries no sentence about GitHub secret scanning and push protection, and
  AC14 is not proven.
- **Deviation 8. These deviations were written after step 12, not one at a time as each happened.**
  Each records what the step's own output showed, which is kept in the build's evidence.
- **Deviation 9. AC6 no longer spells the maintainer's surname.** The verifier found that the
  check wrote the surname as a split literal, which would leave it in the public history once the
  branch is merged, and no done-when clause asks for that check. It is dropped. The other
  fragments stay because the clause about the personal image name and the first name needs them,
  and both already appear in public history.

## Durable content moved out of this plan
