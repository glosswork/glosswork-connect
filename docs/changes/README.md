# Change plans

One file per in-flight change, at `docs/changes/<NNN>-<slug>.md`, where `NNN` is the GitHub
issue number zero-padded to three digits and `slug` matches the branch name. **This README
is the only permanent resident of this directory.** A plan file lives on its own branch, for
the life of that branch, and is deleted in the change's final commit.

Changes 001 to 003 were numbered by the issues of the kit's private archive, from before it
moved to GitHub. GitHub's numbering starts again at 1, so a reference to one of those says
"archive 001".

The issue carries the *why*. The plan carries the *how*, and it is the thing that gets
approved before any code is written.

## Why a file and not a pull request description

- **It is a diff.** The adversarial pass edits a premise in place and git holds what changed,
  which a text field in a web form does not.
- **Agents can read it.** A plan they cannot open is a plan they will guess at.
- **It survives the session.** A session that ends mid-change hands over a file, not a memory.
- **It dies on purpose.** Deleting it at merge is what stops this directory from becoming a
  second, stale specification.

## Template

```markdown
# NNN: <title, written as what is now true>

| | |
| --- | --- |
| Issue | #NNN |
| Branch | `NNN-slug` |
| Depends on | what must be merged first, and why |

## Why
## Premises            P1..Pn, each recording how it was established
## What changes
## What does not change
## Constraints         the invariants execution must not violate
## Checklist           ordered; step 1 is always "run the new assertions against the
                       unfixed tree and record how each failed"
## Accept              AC1..ACn, each a runnable command
## Adversarial pass    F1..Fn with a disposition each
## Deviations from the approved plan
## Durable content moved out of this plan
```

Write a placeholder path with angle brackets, as docs/changes/&lt;NNN&gt;-&lt;slug&gt;.md, and
never as a backticked path with letters in it, so that a placeholder is never mistaken for a
citation of a file that should exist.

## Writing premises

A premise records **how it was established**, in the premise itself: "read at
`.claude-plugin/plugin.json`", "measured by running `claude plugin validate . --strict`",
"reproduced in Claude Code against a scratch configuration directory". A premise inherited
from another issue's prose is the weakest kind. Re-establish it.

Premises about a harness are the ones that rot. Harness versions move weekly, and a fact
read from a documentation page six weeks ago is not a premise. Name the version you tested
and the date you read the page.

## Writing Accept criteria

Every criterion is a command someone else can run. Not a description of a command.

- **Run every new assertion against the unfixed tree first, in the order written.** An
  assertion that has never failed has never been measured.
- **A fence is not coverage.** An assertion guarding behavior the change deliberately does
  not alter cannot fail there by construction. Label it a fence and do not count it.
- **`!` applies to a whole pipeline.** `! grep A path | grep -v B` tests `grep -v`'s exit
  status, which is rarely what was meant.
- **`grep -r` on a missing directory exits 2**, which `!` turns into a pass. Guard a path a
  build produces with `test -d` first.
- **A criterion about a harness names the harness's version**, because the next run of the
  same command against a newer harness is a different measurement.
