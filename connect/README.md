# The connect command

**Deferred.** Codex, Cursor and VS Code connect with documented snippets until this ships.

## What it is for

One command that asks for the workspace address and an access token, checks both by calling
the server before it writes anything, then writes each detected harness's configuration with
that harness's own agent label.

## What the change that builds it has to establish

- It refuses a wrong address or a wrong token with a message naming which one is wrong,
  because it calls the server first. A connect command that writes a broken configuration
  and reports success is worse than no command.
- Where the token ends up on disk, per harness, stated plainly in the pull request. The
  obvious third-party wrapper writes it world-readable and cannot use VS Code's password
  prompt, which is why this is ours rather than a wrapper.
- Each harness's written configuration matches that harness's documented schema, at a named
  version.
- Each writer has a test.
