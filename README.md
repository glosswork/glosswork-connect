# Glosswork connection kit

Everything a person installs to connect an agent harness to a Glosswork workspace. The
product itself, the server with the MCP endpoint, lives in a separate repository. The kit
is separate so that work on it never queues behind product work.

This repository is private until the site is live. Until then a pilot installs from a
local clone or from a file sent to them.

## The pieces

| Path | Piece | For | Status |
| --- | --- | --- | --- |
| `.claude-plugin/marketplace.json` | The kit's own plugin marketplace | Claude Code, added from a local clone | Proven in Claude Code 2.1.274 |
| `.claude-plugin/plugin.json`, `.mcp.json` | The `glosswork` Claude Code plugin: it asks for the address and the token, and sets the agent label | Claude Code | Proven in Claude Code 2.1.274 against a running workspace: two prompts, connected, tools listed |
| `skills/` | Agent Skills, starting with schema design | Every harness that reads a `SKILL.md` | Schema design carries the approved guidance text, pinned by hash, and loads in Claude Code 2.1.274 |
| `mcpb/` | The Claude Desktop extension, a `.mcpb` bundling a pinned proxy | Claude Desktop, against a workspace on the person's own machine or their own network. **A plain `http://` address on a network sends the access token across it in clear text**, which [`mcpb/README.md`](mcpb/README.md) explains in full | Built and proven against a workspace by the harness tests; not yet installed in Claude Desktop |
| `connect/` | One connect command that asks for the address and the token, checks them, then writes each harness's config | Codex, Cursor, VS Code | Deferred |
| `wrappers/` | Thin wrappers that carry the skills folder and no credential | Agent Plugins package, Gemini CLI extension, Pi package | Not built |

The repository root is itself the plugin, so `skills/` is both the kit's skills folder and
the plugin's. `mcpb/`, `connect/` and `wrappers/` are ordinary directories that the plugin
loader ignores.

## What connects without any of this

A hosted workspace is reached from Claude Desktop, Cowork, claude.ai and Claude mobile
through Claude's own "Add custom connector" dialog: paste the address, then paste the token
as an `Authorization` header, with the agent label as a second header. No plugin, no
extension, no OAuth. The kit exists for Claude Code, and for a workspace running on the
person's own machine, which that dialog cannot reach.

## Connecting Claude Code

Measured on Claude Code 2.1.274 on macOS, on 2026-09-17, against a running workspace.

1. Add the marketplace: `claude plugin marketplace add <path to a clone of this repository>`.
2. In a Claude Code session, run `/plugin install glosswork@glosswork` and choose user scope.
   Claude Code asks for two values, "Workspace address" and "Access token", and nothing
   else. Running `claude plugin install` from a shell does not ask: it installs the plugin
   without its values, and `/plugin configure glosswork@glosswork` in a session supplies
   them.

The token field is masked once it loses focus. While the field has focus, as the token is
typed or pasted, Claude Code shows its last six characters in clear and the rest as `*`. The
plugin cannot change that: marking the value sensitive is the only control a plugin has, and
it is set.

Claude Code keeps the token in the macOS login Keychain, not in a file. With
`CLAUDE_CONFIG_DIR` set, the item is `Claude Code-credentials-` followed by eight hex
characters derived from that directory's path. The configuration directory's
`settings.json` holds only the address, and no `.credentials.json` is created. Claude Code's
plugins reference says a sensitive value falls back to `.credentials.json` in the
configuration directory when the Keychain rejects the write, and that the Keychain storage it
shares with the Claude sign-in holds roughly 2 KB. Other operating systems were not measured.

The token survives a restart: a new session connects without asking again, so
anthropics/claude-code#62442 did not reproduce on 2.1.274. The server connects with no
approval dialog, and every request it sends carries `X-Agent-Label: claude-code`, the label a
workspace records on a write sent with it. That header takes precedence over a label on the
token itself.

## Connecting Claude Desktop

The extension is a `.mcpb` file. Build it, then open it: Claude Desktop installs it and asks
for the two values. Everything below was measured by the kit's harness tests against a
running workspace on 2026-09-18. It has not been installed in Claude Desktop yet, and the
table above says so.

```
bash mcpb/build.sh
```

The script writes `mcpb/dist/glosswork.mcpb` and prints the path, the byte count and the
SHA-256. **Two runs of it produce two files with different digests**, so a digest identifies
one built file rather than the content of a build. Install the file whose digest was
recorded rather than building your own and comparing them. **The bundle is unsigned**, so
Claude Desktop may warn about an unsigned extension or an unknown developer at install time.

Claude Desktop asks for the workspace address and an access token, and nothing else. The
token is marked sensitive, so the field is masked and the value goes to the operating
system's secure storage. It reaches the bundled proxy through the environment variable
`GLOSSWORK_TOKEN`, never as a literal in an argument list.

**Spell the address the way the workspace does.** A workspace started with `GW_BASE_URL`
matches the MCP `Host` header against that exact `host:port`, so `localhost:8150` and
`127.0.0.1:8150` are different addresses to it. The wrong one fails with `Invalid Host
header` and status `421`, a message that names neither the address nor the fix and looks
nothing like a token problem. Use the address the workspace prints at startup, spelled the
same way, ending in `/mcp`.

**A plain `http://` address that is not on this machine sends the token across the network
in clear text.** The bundle passes `--allow-http`, so a workspace on your own network is
reachable, and the accepted cost is that the `Authorization: Bearer` header carrying the
token crosses that network unencrypted, where anything on the same wire or access point can
read it. Prefer a workspace on your own machine, where the traffic never leaves it.

**An HTTPS address works only when its certificate already chains to a store Node trusts.**
A self-signed or private-CA certificate is refused, and the extension has no way to be told
about one, because that would mean a third value.

**A wrong, empty, absent or expired token fails with the workspace's own wording and opens
no browser.** That holds because the workspace answers a bad token with HTTP 200 and a
JSON-RPC error rather than a `401`, so the proxy never starts an OAuth flow. It is the
product's behaviour rather than the bundle's, and it changes when a workspace becomes its
own authorization server. If the proxy ever does enter that path it opens a listening socket
on loopback and logs `OAuth callback server running at http://127.0.0.1:<port>`; a
connection that works never reaches it.

[`mcpb/README.md`](mcpb/README.md) carries the table of which addresses the extension
reaches, the clear-text warning in full, and how to run the harness tests.

## One credential, and where it comes from

Every harness connects with an access token that the person creates on their workspace's
Setup page after signing in, named for the tool it is for. The token never travels through
a chat. Nothing in this repository ever contains a real token, and a test enforces that.

## Guidance travels with the server first

The schema guidance text has one owner, the product repository, and reaches every harness
through the MCP server itself, with nothing installed. The skills folder here is the second
channel, for harnesses that load skills but do not surface prompts. This repository keeps a
copy and a check that fails when the copy drifts from the original.

## License

MIT. See [LICENSE](LICENSE). The server keeps its own, different license: the kit is
permissive so that it is accepted wherever it has to be listed, and the copied guidance
text is MIT here.

## Where the repository URL lives

Only in this file. The plugin manifests name no host: the marketplace refers to the plugin
by a relative path, so the same commit works from a clone of any remote. That is deliberate:
a manifest that names a host has to change whenever the host does, and a clone of any
remote should install the same way.

- Source of truth: `https://github.com/glosswork/glosswork-connect`

The kit's history before it moved here is kept in a private archive. This repository
starts from one commit whose tree is that archive's last tree.

CI is the one host-specific file. `.github/workflows/ci.yml` runs three jobs on every push
to `main` and every pull request: `lint` (`ruff check .` and `ruff format --check .`, as
two steps), `test` (`pytest -q`), and `secrets`, which runs gitleaks over every commit and
fails on a finding, and fails on any commit not authored and committed as
`hello@glosswork.dev`. `main` requires all three to pass.

## Working here

Read [AGENTS.md](AGENTS.md) first, then [CONTRIBUTING.md](CONTRIBUTING.md).
