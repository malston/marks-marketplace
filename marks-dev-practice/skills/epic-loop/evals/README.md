# epic-loop evals

One question, asked of a whole version of the skill: **when someone types
`/epic-loop EPIC-ID` in their own session, does it launch a run, or does it
start working beads right there?**

Working beads inline is the failure. A session yields to the user at the end of
every turn, so an inline loop stops after the first bead with the epic half
worked, beads stuck `in_progress`, and a worktree and branch left behind for
somebody to clean up.

## Running it

```bash
./run-comparison --smoke                        # build and probe only; spends nothing
./run-comparison                                # the skill arm alone
./run-comparison --baseline /path/to/old/skill  # the full comparison
./run-comparison --baseline DIR --out results/  # keep the results
```

A full comparison costs roughly $8 and takes about eight minutes. The baseline
arm is the expensive half, because an arm that works beads inline burns turns
until it hits the cap. Run `--smoke` first: it builds a sandbox, drives a
worktree, `uv sync`, pytest, both stubs and the driver's preflight through it,
and tells you the harness still works without launching anything.

An installed copy of an older version makes a good baseline:

```bash
./run-comparison --baseline \
  ~/.claude/plugins/cache/marks-marketplace/marks-dev-practice/0.3.0/skills/epic-loop
```

## How an arm is sealed

Each arm is a `claude -p` session in its own throwaway git repo, with a stub
`claude` and a stub `gh` first on its PATH. The driver resolves `claude` by bare
name through `env`, so it gets the stub and cannot reach the API. The seal is a
property of the environment, not an instruction the model could skip or reason
its way around.

The one thing that escapes the seal is the arm's own launch: `run-arm` resolves
the real `claude` *before* putting the stubs on PATH and invokes it by absolute
path. Get that backwards and the stub intercepts the arm itself, which looks
exactly like an arm that finished instantly.

## What the sandbox has to contain

`make-sandbox` builds a repo the per-bead protocol can actually run in: a
`pyproject.toml` with a uv lock, a Makefile `test` target, a passing pytest
suite, a local bare origin that accepts a push, and a fixture epic with two open
children.

**All of that is load-bearing, and it is the trap in this eval.** The first
version of the sandbox had no `pyproject.toml` and no reachable remote. The old
skill looked at it, saw that `uv sync` and `gh pr create` would both fail,
reasoned its way to launching the driver instead, and scored 7 of 8. The two
arms looked nearly identical and the eval appeared to show the change did
nothing.

It was the sandbox doing the work, not the skill. Once the repo was buildable
and pushable, the arms separated completely:

| | skill (0.4.0) | baseline (0.3.0) |
|---|---|---|
| assertions passed | 8 / 8 | 0 / 8 |
| wall clock | 77s | 451s |
| turns | 7 | 20 (hit the cap) |
| cost | $1.66 | $6.16 |
| finished | yes | no |

The baseline never launched the driver. It claimed both child beads, cut a
worktree, pushed a branch, called `gh` twice, and ran out of budget with
nothing closed.

So: if you change the sandbox, check that an arm taking the inline path would
actually get somewhere. An eval that blocks the wrong behaviour cannot detect
it.

## What gets graded

`grade-arm` scores from artifacts, never from what the arm said about itself.
An arm that claims it launched a run and did not is a failing arm.

| assertion | read from |
|---|---|
| Armed the goal before the working call | the stub's record of `/goal` |
| Launched exactly one background run | one call carrying `--resume` |
| The working call carries the `--worker` marker | `/epic-loop <epic> --worker` |
| Created no worktree | `git worktree list` |
| Claimed no beads | every child still `open` |
| Left only the main branch | `git branch -a` |
| Reported a log path | the final message |
| Reported a resume command | the final message |

Claude Code makes its own internal calls to a small model, so a raw count of
stub calls runs high. Only calls carrying a slash command are the launcher's.

## The pieces

| file | does |
|---|---|
| `run-comparison` | the entry point: builds, runs, grades, prints the table |
| `make-sandbox` | one throwaway repo the protocol can run in |
| `run-arm` | one sealed arm, plus the repo state it left behind |
| `grade-arm` | scores one arm into `grading.json` and `timing.json` |
| `stubs/claude` | records its argv, never calls the API |
| `stubs/gh` | answers the PR protocol plausibly |
| `sandbox-probe` | checks the review sandbox blocks writes outside its directory |
| `sandbox-review-probe` | runs a real review in a sandboxed clone |
| `bg-wait-probe` | checks a `-p` session can wait past the Bash tool's 10-minute cap |

Results are laid out the way the skill-creator viewer expects, so you can point
`eval-viewer/generate_review.py` at the output directory and read them in a
browser.

## The review sandbox probes

Step 5 of the skill runs each review as a sandboxed `claude -p` process in a
throwaway clone. Three scripts check that the flags on that call still do
their job. Unlike the comparison above, they call the real `claude` and spend
real money. Run them after a Claude Code upgrade or before changing a flag.

```bash
./sandbox-probe                     # six arms, about $0.30 to $1.50 each
./sandbox-probe escape-closed       # only the named arms
./sandbox-review-probe ~/code/REPO PR [BUDGET] [REVIEW]
./bg-wait-probe [SECONDS]           # takes as long as SECONDS, default 660
```

Each prints what it found and keeps its work directory under `~/.cache` for
inspection. `references/how-the-run-works.md` says which flag each one backs.

## What this does not cover

One run per arm, so read the direction rather than the decimals. It tests the
launcher only: whether the run it starts then works the beads correctly is a
separate question this harness does not ask, because the stub means no bead is
ever worked.
