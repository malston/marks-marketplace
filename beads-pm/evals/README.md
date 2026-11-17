# beads-pm evals

Behaviour tests for the three skills, run by `claude plugin eval`. Each case
builds a throwaway sbxcli repo with a real `bd` database, invokes one skill
the way a user would (`/beads-pm:backlog-audit sbx-56e`), and grades what
happened.

```bash
evals/run-evals                    # whole suite, 1 run per case
evals/run-evals --tag plan-to-beads
evals/run-evals --case backlog-audit-epic-findings --runs 3
evals/run-evals --login            # locally, if a stale ANTHROPIC_API_KEY is exported
```

`run-evals --help` lists every option. With the defaults (claude-sonnet-5-5,
one run per case) a full pass cost $1.08 and took about 4.5 minutes when
measured on 2026-11-16; `--runs 3` cost $3.35.

## Cases

| Case                                | What it pins down                                                                                                                      |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| backlog-audit-epic-findings         | Dispatches backlog-auditor, relays all five planted faults, invents no cycle, says the epic is not safe to run, changes nothing        |
| backlog-audit-no-epic-id-asks       | With no epic id, asks before a whole-backlog audit                                                                                     |
| backlog-groom-first-bead-then-stop  | Without approval, judges by clause and proposes, but writes nothing                                                                    |
| backlog-groom-approved-runs-through | With approval, tags the retry/backoff decision `human`, sets no priority, stops at the limit, ends with the summary                    |
| plan-to-beads-first-look            | Shows the shape numbers, flags both design decisions, asks for approval, files nothing                                                 |
| plan-to-beads-approved-file-through | With approval, files through backlog-filer, then audits with backlog-auditor; the filed graph has the right children, edges and labels |

## How grading works

`claude plugin eval` has no command graders, so the backlog's state is graded
two ways:

- **Must not write.** A `regex` grader on the trace fails the case if any Bash
  call, including one made inside a subagent, ran a `bd` write verb
  (`create`, `update`, `close`, `label add`, `dep add`, ...). It matches
  the JSON `"command"` field only, so skill text that merely mentions
  `bd cleanup` does not trip it. This was checked against runs that do write.
- **Must write the right thing.** The two "approved" cases end their prompt by
  asking for `bd export -o post-state.jsonl`; graders read that file.

The threshold is 1.0: a case passes only if every grader passes in every
run. LLM-judged graders are worded so a correct answer in any reasonable shape
passes; when one fails, read the evidence in `report.html` before blaming the
skill. Several early failures were the judge reading a criterion more strictly
than intended.

## What it does not cover

- **Triggering.** Every case invokes the skill by slash command, so these
  evals say nothing about whether a skill's description makes Claude pick it
  up unprompted.
- **The two "stop and wait" cases barely separate the skill from the base
  model.** Copies of plan-to-beads with "Show the shape, then stop" deleted, and
  of backlog-groom told to apply changes without asking, still stopped and
  wrote nothing. plan-to-beads-first-look failed only on the missing shape
  numbers. A green run shows the model behaves; it does not prove the skill's
  stop rule is doing the work.

## Fixtures

`fixtures/setup-repo.sh` is shared by every case's `scaffold.sh`:

- `backlog`: imports `sbx-backlog.jsonl`, epic `sbx-56e` with seven children
  and planted faults: a stale edge from .5 onto the closed sbx-0um, decision .4
  filed as a task, .6 duplicating .1, oversized .7, and .5 naming no files or
  test.
- `plan`: an empty backlog plus `plan.md`, a six-item plan for an sbxcli
  `sync` subcommand with two open design decisions and one out-of-scope
  follow-on.

Both get `.claude/definition-of-ready.md` with the project specifics filled in.

## Adding a case

Copy the nearest case directory, change `name`, the prompt and the graders.
Grade state through the trace regex or a `bd export` file rather than an LLM
reading the final message; the final message reports what the model believes
it did. Run it with `--runs 3` before trusting it, and check a deliberately
broken skill makes it fail.
