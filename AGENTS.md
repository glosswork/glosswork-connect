# AGENTS.md

Instructions for any coding agent or human working in this repository. This is the
canonical entry point; tool-specific files, if any, point here rather than restating rules.

For what the kit is, read [README.md](README.md). This file is about how to change it.

## What you are working on

The connection kit: the packaging that gets a Glosswork workspace's address and an access
token into an agent harness, plus the Agent Skills that teach an agent to use Glosswork
well. It is packaging and guidance. No product behavior lives here, and nothing here talks
to a database.

## Commands

| Purpose | Command |
| --- | --- |
| Install | `uv sync` |
| Test | `uv run pytest -q` |
| Lint | `uv run ruff check .` and `uv run ruff format --check .`, as two commands |
| Validate the plugin and the marketplace | `claude plugin validate . --strict` |
| Build the Claude Desktop extension | `bash mcpb/build.sh` |
| Run the harness tests | `GLOSSWORK_HARNESS=1 uv run pytest -q -m harness` |

`claude plugin validate` needs the Claude Code CLI, which CI does not carry, so it is a
local gate. Run it whenever you touch `.claude-plugin/` or `.mcp.json`, and say in the pull
request that you did.

The harness tests are a local gate for the same reason: CI's image carries neither Node nor
Docker. They need Docker, Node, the product image and macOS, they start and remove their own
scratch workspace, and they never touch a pilot's. `GLOSSWORK_HARNESS=1` is not optional; see
the trap below.

## Where things are

| Path | Holds |
| --- | --- |
| `.claude-plugin/marketplace.json` | The marketplace a person adds in Claude Code. Refers to plugins by relative path only |
| `.claude-plugin/plugin.json` | The `glosswork` plugin: the two values it asks for, and where they go |
| `.mcp.json` | The MCP server the plugin installs, with the address and token substituted in |
| `skills/` | Agent Skills. One directory per skill, each with a `SKILL.md` |
| `mcpb/` | The Claude Desktop extension |
| `connect/` | The connect command |
| `wrappers/` | Thin wrappers that carry skills to other harnesses |
| `tests/` | Structural tests: their input is the files in this repository, not a running system |
| `docs/changes/` | One plan file per in-flight change. See its README |

## Non-negotiables

These decay silently if not enforced on every change.

1. **No credential ever enters this repository.** Not a real token, not a masked one, not a
   test fixture that looks like one. Values come from the person at install time and are
   substituted by the harness. `tests/test_no_credentials.py` scans every file and fails on
   anything token shaped, and CI's `secrets` job runs gitleaks over every commit and fails on
   a finding.
2. **Never pin a dependency version from memory.** Verify the current stable release on PyPI
   (`uv run --with pip pip index versions <pkg>`) or npm (`npm view <pkg> version`) before
   pinning, then confirm what actually resolved.
3. **The manifests name no host.** The marketplace refers to a plugin by a relative path, and
   the plugin manifest carries no repository or homepage URL, so a clone of any remote
   installs the same way and a change of host is never a change to the manifests. A test
   enforces the relative path.
4. **The guidance text has one owner, and it is not this repository.** The product repository
   holds it. The copy here, `skills/glosswork-schema-design/SKILL.md`, is a copy, and it
   ships with a check that fails when it drifts. Until the product repository carries its
   own copy, `tests/test_guidance.py` pins the approved front matter and body by SHA-256, in
   `APPROVED_FRONT_MATTER_SHA256` and `APPROVED_BODY_SHA256`, and each failure names the part
   that drifted. Once the product repository's copy is merged, the change that points the
   check at that copy retires both hashes. Until then a hash changes only in a change that
   re-pins it to a new approved original. Never edit the copy, or a hash, to fix a
   disagreement; fix the original.
5. **Type-hint new and modified functions, and prefer `pathlib` over `os.path`.** Use `uv`
   with the local `.venv`; do not depend on a global `python3`.
6. **Every behavior change ships with a test**, and in this repository almost every behavior
   is the shape of a file, so the test is usually a structural one.
7. **The token is passed by reference, never by value.** In an MCP configuration the token
   reaches the server through a substitution or an environment variable, never as a literal
   in an argument list, because arguments are visible in the process table.
8. **Every commit is authored and committed as `Glosswork <hello@glosswork.dev>`.** Set it in
   the clone's local config before the first commit (`git config user.name Glosswork` and
   `git config user.email hello@glosswork.dev`), because a global identity is usually a
   personal address, and a personal address in a public repository's history cannot be
   taken back. CI's `secrets` job fails on any commit carrying another identity.

## Traps

Each of these cost this project real time at least once.

- **Read the exit code, not the output.** A command can print a green tally and exit 1.
  Anything that reads a command's output for the answer it expects will miss that class.
- **Reading an exit code through a pipe reads the pipe's.** `cmd | tail -1; echo $?` reports
  `tail`'s status, which is almost always 0. Run the command bare, or redirect to a file and
  read `$?` on the next line.
- **Half a command is not the command.** The lint here is two commands, `ruff check .` and
  `ruff format --check .`. The first passes on its own, which is exactly how the second goes
  unrun for several changes at a time. An Accept block that gates on lint names both and
  reads each exit code separately.
- **A placeholder is not an implementation.** Several directories here hold a README and
  nothing else on purpose. Do not let a plan treat one as built because the path exists.
- **`pytest -m harness` exits 0 when every harness test skips.** A missing Docker, Node,
  image or non-macOS host skips each test, and a run that skipped everything is exit 0 and
  a green tally, which reads exactly like a run that passed. Set `GLOSSWORK_HARNESS=1`, which
  turns a missing prerequisite into a failure that names it. Any gate that claims the harness
  ran sets that variable.
- **The extension's no-browser guarantee is the product's behaviour, not the bundle's.** A
  wrong token opens no browser because the workspace answers it with HTTP 200 and a JSON-RPC
  error instead of a `401`, so the bundled proxy never enters its OAuth path. Nothing in the
  manifest enforces that. When a workspace becomes its own authorization server it will start
  returning `401` with metadata, and the same bundle will open a browser. Re-measure it then
  rather than citing this change.
- **Your own uv configuration can put a private index into `uv.lock`.** `uv lock` records
  the index each package resolved from, and a developer's user-level uv configuration can
  name a private index even when the packages themselves come from PyPI. The lock then
  carries that index's URL, which is a disclosure in a public repository. Lock with
  `UV_NO_CONFIG=1 uv lock`. `tests/test_lockfile.py` fails on any host in the lock other
  than `pypi.org` and `files.pythonhosted.org`.
- **A plugin's paths cannot escape the plugin directory.** There is no `../` in a manifest
  path. That is why the repository root is the plugin root, and why `skills/` sits at the
  top level rather than inside a subdirectory.

## How to work here

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow. In short: one change at a
time, tracked as an issue, executed on a branch, the plan written as a file and approved
before any code, an adversarial pass by someone who did not write the plan, verification
against the Accept block, then one push and one pull request. Do not claim completion from
inspection. Run the commands.
