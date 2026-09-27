# Thin wrappers

**Not built.** Small packages that carry the `skills/` folder to harnesses that read a
`SKILL.md` but package it their own way: an Agent Plugins package, a Gemini CLI extension,
and a Pi package.

## The rule that shapes them

**A wrapper carries guidance and no credential.** The Agent Plugins specification forbids
secrets in headers, and guidance is useful without a connection anyway. A wrapper that
starts asking for a token has turned into the connect command, and belongs there instead.

Each wrapper is a thin manifest over the same skill directories. None of them gets its own
copy of the text.
