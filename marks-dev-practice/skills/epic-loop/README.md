# Epic Loop

`/epic-loop` works every open child of a beads epic, unattended, one bead at a
time. Each bead gets its own worktree, branch and pull request: a failing test
first, a fix, one or two reviews, each in a fresh sandboxed process, a review commit, then a
merge (or a hold for your approval). The run keeps going until every child is
closed, held, or handed back to you.

```text
/epic-loop coderay-cwi --hold --review-budget 5
```

A visual walk-through of the whole flow is at
<https://claude.ai/artifact/FgNeuV9e2CUwmeqXnnHhQa>. Questions an engineer
tends to ask are answered in [docs/faq.md](docs/faq.md).

## When to use it

Use it for an epic (or a feature, or a task with subtasks) whose children are
each a PR-sized piece of work you would be happy to see done without being
asked at every step.

Don't use it for:

- a single bead, or a parent with no open children
- work that needs a human decision at every step
- a repository that isn't tracked with beads

Beads that ask a design or keep-or-delete question are not decided by the run.
It investigates, writes a recommendation into the bead's notes, tags it
`human`, and moves on.

## Requirements

| Tool                      | Why                                                                         |
| ------------------------- | --------------------------------------------------------------------------- |
| `claude` 2.1.272 or newer | Runs the loop; older versions let `/goal` stall silently after an API error |
| `bd`                      | The beads tracker, with parent/child links between beads                    |
| `gh`                      | Opens, checks and merges the PRs                                            |
| `git`, `jq`, `uuidgen`    | Worktrees, JSON parsing, session ids                                        |

The per-bead protocol in `SKILL.md` assumes a Python project run with `uv`
(`uv sync --locked`, `uv run pytest tests/ -q`) and a CI check named
`pytest`. For another stack, put your own protocol in the epic's DESIGN
field; see the FAQ.

Run it from the repository's main checkout, not from a linked worktree.

## Quick start

1. Open a Claude Code session in the repository that holds the epic.
2. Type `/epic-loop <epic-id> --dry-run` to see the plan. It spends nothing.
3. Type `/epic-loop <epic-id> --hold` to start a run that stops each PR at
   ready-for-review.
4. The session prints a banner with the log path and a resume command, then
   stops. The run keeps going on its own, even if you close the session.
5. The run is over when the log's last line reads `finished:` with an exit
   status.

## Options

The session passes these through to the driver untouched.

| Option                | Default                           | What it does                                                            |
| --------------------- | --------------------------------- | ----------------------------------------------------------------------- |
| `--hold`              | off                               | Stop each PR at ready-for-review and mark its bead blocked; never merge |
| `--repo DIR`          | git root of the current directory | The repository whose beads to work                                      |
| `--dry-run`           | off                               | Check the epic and print the exact calls; spends nothing                |
| `--budget USD`        | 200.00                            | Spending cap for the working session and its subagents                  |
| `--review-budget USD` | 10.00                             | Spending cap for each review, on top of `--budget`                      |
| `--max-turns N`       | 400                               | Claude Code's own turn cap on the working session                       |
| `--turn-budget N`     | 20                                | The epic turn counter the run stops at                                  |
| `--model NAME`        | `claude-opus-5`                   | Model for the working session                                           |
| `--log-dir DIR`       | `~/.local/state/epic-loop`        | Where run logs go                                                       |
| `--session-id UUID`   | a new one                         | Reuse a session id                                                      |

Without `--hold`, the run is in merge mode: each PR is merged into `main` as
soon as its review round passes, without asking again.

## What a run does

### Launch

When you type `/epic-loop`, your session does four things and then stops:

1. Finds the driver, `scripts/epic-loop`, in the skill's directory.
2. Runs it with `--dry-run`. The driver refuses a bead that doesn't exist, is
   closed, or has nothing left to work, and refuses to run from a linked
   worktree or with a tool missing.
3. Starts the driver under `nohup`, detached from your session, and waits
   until it prints `working epic:`.
4. Reports the banner: repo, mode, budgets, log path and resume command.

The driver then makes two `claude` calls against one session id:

- **Arming call.** `claude -p "/goal <condition>"` with Bash, the edit tools
  and subagents denied, and a one-turn cap. It records a completion condition
  on the session and does
  nothing else.
- **Working call.** `claude -p "/epic-loop <epic> --worker"`, resuming that
  session. After every turn, `/goal` checks the condition and sends the
  session back to work while it is unmet.

The condition is met when every child is closed, blocked on a held PR, or
tagged `human`, or when the epic's turn counter reaches `--turn-budget`.

### Per bead

1. **Pick and isolate.** Clean up any held PR that has merged since the last
   pass. Pick the next open bead whose files don't overlap an open PR from this
   loop, and create a worktree for it at `.claude/worktrees/<bead-id>` off
   `origin/main`.
2. **Claim and scope.** Claim the bead. If an earlier PR already covered part
   of it, record what was dropped in the PR's "Trimmed" section.
3. **Test first.** Write a failing test, make the smallest fix, then mutate the
   guard both ways and watch the test go red each time.
4. **Open the PR** with the `epic-loop` label and a fixed set of sections, then
   wait for CI.
5. **Review in a fresh process, from a sandboxed clone.** `/code-review
medium` always runs. `/pr-review-toolkit:review-pr` also runs if any bead
   in the PR is P0 to P3. Each review is its own `claude -p` process in a
   throwaway clone, with the strict sandbox on, no edit tools, no MCP servers
   and its own spending cap.
6. **Fix or file.** Fix every Critical, Important or HIGH finding, and any
   correctness or security defect, in one review commit. File the rest under
   a sibling findings epic.
7. **Land or hold.** Merge mode merges with a merge commit, removes the
   worktree and closes the bead. Hold mode marks the bead blocked with a
   `held: PR <n>` note and moves on.

## What a run leaves behind

| Where                       | What                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| The epic                    | Children closed, blocked or tagged `human`; a `turns-N` label counting turns; a `halted:` note if it stopped early |
| `<epic> review findings`    | A sibling epic holding every finding the run filed rather than fixed                                               |
| GitHub                      | One PR per bead, labeled `epic-loop`, with the review round, trims and open decisions in its body                  |
| `.claude/worktrees/`        | Removed after a merge; kept for a held PR until it lands                                                           |
| `~/.local/state/epic-loop/` | One log per run, ending in a `finished:` line                                                                      |

Your main checkout's branch is never switched, and the run never uses a bare
`git stash`, since the stash is shared across worktrees.

## Safety

- **Your checkout.** Before and after each review, the run records the HEAD,
  branch and branch list of your main checkout and the bead's worktree, plus
  the worktree's uncommitted files. Any change stops the run. Your checkout's
  uncommitted files are left out, since you may be editing while it works.
- **Reviewers.** A reviewer runs in a clone, so a checkout there can't move
  your repository. The sandbox refuses Bash writes outside the clone, including
  a retry with the sandbox turned off. `references/how-the-run-works.md`
  explains the gap each setting closes; the probe scripts in `evals/` re-run
  the tests.
- **The worker is not sandboxed.** The working session runs with
  `--permission-mode bypassPermissions` so it can work unattended. It has the
  access you have in that repository.
- **Billing.** The driver strips `ANTHROPIC_API_KEY` and
  `ANTHROPIC_AUTH_TOKEN` from both calls, so a key exported by the repo or your
  shell doesn't quietly move the run onto a pay-as-you-go account.
- **Never.** The run never edits a bead's title or description, files a
  finding under the epic being worked, merges in hold mode, or bumps a version.

## Files

| Path                              | What it is                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------- |
| `SKILL.md`                        | The instructions both the launcher and the worker follow                          |
| `scripts/epic-loop`               | The driver: checks the epic, arms the goal, starts the working call, logs the run |
| `scripts/epic-loop-test`          | Unit test for the driver, with `claude` stubbed                                   |
| `scripts/label-findings`          | Asks a model to label each filed finding, to measure it against what happened     |
| `scripts/label-findings-test`     | Unit test for `label-findings`                                                    |
| `references/how-the-run-works.md` | The plumbing: the two calls, budgets, the API key, the review sandbox             |
| `evals/`                          | End-to-end checks of the launcher, plus probes for the review sandbox             |
| `docs/faq.md`                     | Questions and answers                                                             |

## Testing changes

```bash
scripts/epic-loop-test --repo <a beads workspace>   # driver, spends nothing
evals/run-comparison --smoke                         # eval harness, spends nothing
evals/run-comparison                                 # launcher eval, about $2
```

`evals/README.md` covers the eval harness and the sandbox probes.
