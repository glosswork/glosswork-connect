# The Claude Desktop extension

A `.mcpb` bundle that connects Claude Desktop to a Glosswork workspace. It asks for two
values, the workspace address and an access token, and replaces hand-editing
`claude_desktop_config.json`.

## What it is for

A `.mcpb` runs a local process, so it is the path to a workspace that Claude's own
connector dialog cannot reach: one on the person's own machine, including `localhost`,
or one on their own network. A hosted workspace does not need it, and Cowork's cloud
sessions cannot reach a private address at all.

The bundle ships no code of ours. It is a manifest plus `mcp-remote`, pinned to an exact
version, which speaks stdio to Claude Desktop and streamable HTTP to the workspace.

## The two values

| Value | What it is |
| --- | --- |
| Workspace address | The workspace's MCP address, ending in `/mcp` |
| Access token | A token created on the workspace's Setup page, named for this extension |

The token is marked `sensitive`, so Claude Desktop masks the field and keeps the value in
the operating system's secure storage. It reaches `mcp-remote` through the environment
variable `GLOSSWORK_TOKEN` and never as a literal in an argument list, because arguments
are visible in the process table.

## A plain HTTP address on your network sends the token in clear text

The bundle passes `--allow-http`, so an address like `http://192.168.1.20:8000/mcp`
works and a workspace on your own network is reachable. **The cost is real and it is
accepted deliberately.** On a plain `http://` address the `Authorization: Bearer` header
carrying your access token crosses that network unencrypted, where anything else on the
same wire or the same access point can read it. Use such an address only on a network you
trust, prefer a workspace on your own machine where the traffic never leaves it, and if a
token may have been exposed, delete it on the Setup page and create another.

The same warning is on the address field itself, which is what Claude Desktop shows while
you are choosing an address.

## Which addresses it reaches, and which it does not

| Address | Works | Why |
| --- | --- | --- |
| `http://127.0.0.1:PORT/mcp` or `http://localhost:PORT/mcp` | Yes | On this machine, nothing leaves it |
| `http://<a name on your network>:PORT/mcp` | Yes | `--allow-http`, with the warning above |
| `https://<anything>/mcp` with a certificate this machine already trusts | Yes | Node verifies it normally |
| `https://<anything>/mcp` with a self-signed or private-CA certificate | **No** | Node refuses it with `self-signed certificate`, and the extension has no way to be told about a certificate: that would be a third value, and the whole promise here is two |

## Spell the address the way the workspace does

A workspace started with `GW_BASE_URL` matches the MCP `Host` header against that exact
`host:port`. So `localhost:8150` and `127.0.0.1:8150` are **different addresses**, even
though they are the same machine, and the wrong one fails with:

```
Error POSTing to endpoint: Invalid Host header
status: 421
```

That message names neither the address nor the fix, and it looks nothing like a token
problem. Use the address the workspace itself prints at startup, spelled the same way,
with `/mcp` on the end.

## Building it

```
bash mcpb/build.sh
```

It writes `mcpb/dist/glosswork.mcpb` and prints the path, the byte count and the SHA-256.

**The build is pinned, not reproducible.** Packing the identical directory twice gives
two files of the same size with different digests, so a printed digest identifies one
built file rather than the content of a build. Install the file whose digest was
recorded, rather than building your own and comparing.

**The bundle is unsigned.** `mcpb` has `sign` and `verify` commands and this build uses
neither, so Claude Desktop may warn about an unsigned extension or an unknown developer
at install time. That is expected.

## Two things it does on your machine

- If `mcp-remote` ever enters its OAuth path it opens a listening socket on loopback,
  logging `OAuth callback server running at http://127.0.0.1:<port>`. A normal connection
  never reaches that path.
- A wrong, empty, absent or expired token fails with the workspace's own wording and
  **opens no browser**. That holds because the workspace answers a bad token with HTTP 200
  and a JSON-RPC error rather than a `401`, so the proxy never starts an OAuth flow. It is
  the product's behaviour rather than the bundle's, and it would change if a workspace
  became its own authorization server.

## Tests

The structural tests, `tests/test_mcpb_manifest.py`, run in CI. What the built bundle does
against a real workspace is `tests/test_mcpb_bundle.py`, which needs Docker, Node, the
product image and macOS:

```
GLOSSWORK_HARNESS=1 uv run pytest -q -m harness
```

The environment variable is not optional. Without it a missing prerequisite skips, and the
command exits 0 on a machine that ran nothing.

Anthropic's directory terms for `.mcpb` submissions carry non-waivable open-source and
"spec will evolve" clauses. The kit is MIT, which satisfies the first.
