# Contributing

This project is maintained through GitHub issues and pull requests. It uses the same
process as the Glosswork product repository, for the same reasons: every step exists
because skipping it cost real time at least once.

Read [AGENTS.md](AGENTS.md) first. It carries the commands, the non-negotiables and the
traps. This file is only about process.

## Roles

**Maintainer** means Heavylift Labs, which publishes Glosswork. The maintainer approves a plan before it is executed, and
approves and merges the pull request afterward.

## One change at a time

1. **Open an issue.** It carries the *why*: the problem, and the evidence that it is real.
   Use the `Change` or `Bug` template, in `.github/ISSUE_TEMPLATE/`.

2. **Branch from `main` and write the plan as a file**, at `docs/changes/<NNN>-<slug>.md`,
   where `NNN` is the issue number zero-padded to three digits. Commit it **alone**, as
   `NNN: plan`. `docs/changes/README.md` holds the template and the rules. The plan is the
   thing that gets approved, so it must be concrete enough to argue with.

3. **Everything from here to step 7 happens locally.** Do not open a pull request yet. A
   branch is pushed once, when the change is finished and verified.

4. **Run an adversarial pass over the plan before executing any of it.** Try to falsify your
   own premises. Findings go into the plan's own "Adversarial pass" section as `F1..Fn`, each
   with a disposition, and the fixes are folded into the plan text in place.

5. **Get the plan approved as written.** Amendments are folded into the plan by editing the
   affected text in place, not appended as a log. The file should always read as the current
   plan, and git holds what changed.

6. **Execute in checklist order.** A deviation is recorded in the plan's "Deviations" section
   as it happens, not reconstructed afterward.

7. **Verify independently, locally.** Run the Accept block as written, not the checklist item
   you remember executing. Keep the output. Do not assert completion from inspection.

8. **Close it out in the final commit.** Move what stays true into `README.md` or `AGENTS.md`,
   then delete the plan file, keeping a copy of its final text.

9. **Push once, and open the pull request once**, not as a draft, using the pull request
   template in `.github/pull_request_template.md`. Its description carries the plan's final
   text, the Accept output, every deviation and the closeout. One push, one pull request,
   one CI run. The maintainer merges.

## Branches and commits

- Branch from `main`, named for the issue: `12-short-kebab-description`.
- Commit messages start with the issue number: `12: the plugin asks for two values`. Write
  the subject as what is now true, not as what you did.
- `main` is protected. Everything lands by pull request, and the `lint`, `test` and
  `secrets` checks must pass first; the protection applies to administrators too. GitHub
  cannot tell an agent from the maintainer, because the agent's token acts as the
  maintainer's own account, so "the maintainer merges" is a rule that GitHub does not
  enforce.
- The `secrets` check runs gitleaks 8.30.1, downloaded and checked against its published
  SHA-256, over every commit on every branch the CI checkout fetched, not only the pull
  request's, and fails on any finding. The same job fails on any commit that is not authored
  and committed as `hello@glosswork.dev`; GitHub's own committer on a merge made in its web
  page is allowed. On a pull request run it examines the pull request's own commits and
  ignores the temporary merge commit GitHub makes for the run, which is authored as
  whichever account opened the pull request and never enters the history. On a push to
  `main`, or a run started by hand, it examines the whole checked-out history, merge commits
  included. It fails on a shallow checkout, on a run that examined no commits, and on any
  other event.
- GitHub's own secret scanning and push protection are turned on for this repository, in its
  settings, as the maintainer configured them. They are settings, not files, so nothing in
  this repository proves them, and the `secrets` check above is the gate that the code does
  prove.
- A merge in the web page uses "Create a merge commit", with `hello@glosswork.dev` chosen as
  the commit email, never squash or rebase, so the merge commit is authored as
  `hello@glosswork.dev` and committed by GitHub.
- One exception is already spent: the first commit on GitHub, which moved the kit here as
  one commit and therefore could not come through a pull request.

## What a pull request must carry

- The plan's final text, with its checklist ticked.
- The Accept block, with the output of the commands that prove it.
- A note of every deviation from the approved plan, and why each was right.
- Green CI.
- For any change to `.claude-plugin/` or `.mcp.json`: confirmation that
  `claude plugin validate . --strict` passed locally. CI has no Claude Code CLI, so the
  pull request is the only place that check happens.
- For any change that connects a harness for real: the harness, its version, and where the
  token ended up on disk.

## Tests

Every change ships with a test, and here almost every test is structural: its input is a
file in this repository rather than a running system.

- **Every assertion must be able to fail.** Run a new assertion against the unfixed tree and
  watch it fail before you fix anything.
- **Retire superseded assertions as part of the change.** Keeping a test that asserts the
  shape the change decided against asserts two contradictory outcomes at once.
- **A test that proves a harness connects is worth more than ten that prove a file parses.**
  The file tests are the floor, not the target.

## Working with AI coding agents

- **Name the exact document and section an agent must read.** Never ask an agent to figure
  out the design. If it needs a design decision, it stops and reports rather than choosing.
- **The plan is written by one session and executed by another.** An adversarial pass is
  worth most when it is read by something that did not write the premises.
- **Hand the implementing session one goal at a time**, naming the plan file, the sections to
  read, what must not change, and the command that proves it done.
- **The verifying session runs the Accept block and reports `PASS`, `FAIL` or `NOT PROVEN`.**
  `NOT PROVEN` means no test exists at all, and it is a distinct and important outcome.

Agent-authored changes go through the same issue, plan, approval and pull request path as
any other. There is no fast lane.

## Reporting a security issue

Do not open an issue for a vulnerability. Mail the address on the Glosswork security page.
