<!--
This pull request is opened ONCE, when the change is finished and verified, and not as a
draft beforehand. See CONTRIBUTING.md.

By the time you open this, the plan file is already deleted, its durable content moved into
README.md or AGENTS.md. Paste the plan's final text below: a file added and deleted on one
branch never appears in this diff, so this is the only place it lands.
-->

Closes #

## Plan

<!-- The plan's final text, as executed. Not a summary, and not a link to a deleted file. -->

- Adversarial pass: <!-- findings F1..Fn, or "none found", and who ran it -->
- Plan approved by: <!-- and where -->

## Accept

<!--
The OUTPUT of the Accept block, run as written, before this pull request existed. Every
criterion is a command. Say which criteria are fences.
-->

```
```

## Local checks CI does not run

- [ ] `claude plugin validate . --strict` passed, for any change to `.claude-plugin/` or
      `.mcp.json`
- [ ] The harness was actually driven, for any change that claims a harness connects:
      name the harness, its version, and where the token ended up on disk

## Credentials

- [ ] No token, key or configuration file carrying one appears in the diff, the description,
      or a screenshot
- [ ] Any new value a person supplies is marked sensitive and reaches the server by
      substitution or environment variable, never as a literal argument

## Deviations from the approved plan

<!-- Every one, with why it was right. "None" is a valid answer, but it is an answer. -->

## Closeout

- [ ] Durable content moved into `README.md` or `AGENTS.md`
- [ ] Superseded assertions retired, not left contradicting the new ones
- [ ] Plan file deleted in the final commit, its final text pasted above
