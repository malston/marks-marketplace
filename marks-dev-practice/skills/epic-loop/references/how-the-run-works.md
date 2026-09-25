# How the run works

The plumbing behind `/epic-loop`. Read this when the driver misbehaves, when
you want to start a run from a plain shell, or when you are changing the
driver. Nobody needs it to use the skill.

## The two calls

A run is two `claude` calls against one session id, in this order.

```bash
SID="$(uuidgen)"

claude -p "/goal <condition>" --session-id "$SID" --max-turns 1 \
    --disallowedTools "Bash,Edit,Write,NotebookEdit,Task,Agent"

claude -p "/epic-loop <bead-id> [--hold] --review-budget 10.00 --worker" --resume "$SID" \
    --permission-mode bypassPermissions --max-turns 400
```

Both are required, and the order matters, for three reasons.

The CLI expands only the **first** slash command in a prompt. Everything after
it becomes that command's arguments, so a `/goal` on a later line is dead text.
The two cannot share one call.

The skill sets `disable-model-invocation: true`, so the model will not reach
either command on its own. They have to be typed.

The arming call is denied every tool that can change the repository and capped
at one turn. Without that it starts satisfying the goal in the arming call
itself, working beads before the loop protocol is loaded. The goal is still
recorded, and it survives both the cap and the denial.

So a healthy arming call ends on `Reached max turns (1)` and exits 1: `/goal`
tells the model to start working, and its first tool call spends the one turn.
An auth or credit failure exits 1 as well, so the driver asks for
`--output-format json` and reads the result instead of the exit code. A
`subtype` of `error_max_turns`, or a `success` with `is_error` false, lets the
run go on, and the log says the cap was expected. Anything else stops the run
before the working call, with the result's message on stderr and in the log.

The goal carries into the resumed working call and re-evaluates after every
turn there: when the model stops, the condition is checked, and while it is
unmet the model is re-prompted to work the next bead. Confirmed by
reproduction, arm-then-resume in `-p` mode against a stub goal, on 2.1.270 and
2.1.272. It needs Claude Code 2.1.272 or newer, though: 2.1.272 fixed `/goal`
silently stalling after API errors, network drops, or token limits. On an older
claude the loop can stop evaluating mid-run, and the session then exits at its
next natural stop with the epic unfinished, reading as a clean finish. The
driver refuses to start below that version.

The condition to arm:

```text
/goal Every open child of beads epic <bead-id> is closed, blocked on a held PR, or tagged `human`, worked per /epic-loop; or stop when the epic's turn counter reaches 20
```

The backticks around `human` must stay literal. In a shell that builds this
string, escape them. Unescaped, bash runs `human` as a command, the
substitution yields nothing, and the condition quietly loses the word, which is
how a human-tagged bead stops counting as settled.

## The run marker

`--worker` on the second call tells the skill the session is the run. Without
it the skill starts a run instead of working beads, which is exactly what it
should do when a person types `/epic-loop` in their own session. A working call
that lost the marker would spawn a driver, which would spawn a driver.

To work an epic in your own interactive session rather than a background one,
arm the goal with `/goal <condition>` and then type `/epic-loop <bead-id>
--worker`. The marker is what tells the skill you meant this session. Expect to
prompt it between beads: a session yields to you at the end of every turn, and
only the `-p` calls above run unattended.

## Three different budgets

`--max-turns` is Claude Code's own cap on the working call, a runaway stop. The
loop spends turns fast: one bead runs a failing test, a mutation round, a PR, a
fresh-context review and a fix commit.

The turn counter in the goal condition is a different number. It lives in the
parent bead as a `turns-<N>` label so a resumed session does not reset it, and the skill
rewrites it at the end of every turn.

`--budget` is a third limit, in dollars, and it does not cover everything. It
becomes `--max-budget-usd` on the working call, which counts that session and
its subagents. Each review in step 5 is a separate `claude -p` process with its
own cap, set by `--review-budget` (default $10), which the driver passes to the
skill in the working prompt. Reviews spend on top of `--budget`: up to four
times `--review-budget` a bead, when both reviews run and each is retried once.
The $10 default is a guess with headroom: the only measured reviews, on a
one-line PR, cost $0.33 to $1.01.

## The API key

Both calls run from inside the target repository. A repository that exports an
Anthropic key for its own tooling -- a direnv `.envrc`, a sourced `.env` -- or a
shell that exports one globally, hands it to `claude` too, where it outranks
the claude.ai login. The run then bills a pay-as-you-go account and can die on
"Credit balance is too low" before working a single bead.

The driver strips `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` from both
calls. Set `EPIC_LOOP_KEEP_API_KEY=1` when that account is the one you mean to
spend. **Typing the calls by hand carries the same risk**, so prefix them with
`env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN`.

## The review process

Step 5 of the skill runs each review as its own `claude -p` process, started
inside a throwaway `--shared` clone under `${TMPDIR:-/tmp}/epic-loop/`. A
review agent dispatched from the worker used to inherit the worker's working
directory, which drifts back to the main checkout on its own, and
`/code-review` checked out a PR branch there. A process started in a clone has
no directory to drift from, and a checkout inside the clone moves only the
clone.

Each flag on that call closes a gap that a test on Claude Code 2.1.281 (macOS)
showed was open:

- `sandbox.enabled`: Bash commands can write only inside the clone and the
  session temp directory. It holds under `--permission-mode bypassPermissions`,
  and it covers subagents the reviewer starts.
- `sandbox.allowUnsandboxedCommands: false`: without it, a command that fails
  in the sandbox can be retried with `dangerouslyDisableSandbox`, and under
  bypass mode that retry runs unsandboxed with nothing asking first.
- `sandbox.failIfUnavailable: true`: a sandbox that cannot start otherwise
  falls back to running commands unsandboxed, with only a warning.
- `--disallowedTools "Edit,Write,NotebookEdit"`: the sandbox covers Bash only.
- `--strict-mcp-config`, with no `--mcp-config`: MCP tools run outside the
  sandbox. With user settings loaded, a reviewer had 247 of them, including
  ones that push, merge and send mail; with this flag it had none.
- `--setting-sources user`: keeps the user's plugins, which supply the review
  commands, and skips project and local settings, so hooks committed on the PR
  branch never run.
- `--max-budget-usd`: a separate process is outside the driver's
  `--max-budget-usd`, which covers the worker and its subagents only. See
  [Three different budgets](#three-different-budgets).

Command-line `--settings` outrank user, project and local settings, so a
user-level `allowUnsandboxedCommands: true` does not reopen the retry.

The sandbox blocks `gh` on macOS: Go tools need the system TLS trust service
(`com.apple.trustd.agent`), and `gh` fails with `x509: OSStatus -26276`.
`sandbox.enableWeakerNetworkIsolation` would open it, along with an
exfiltration path, so it stays off. The worker fetches the PR branch into the
clone before the review starts, and `--append-system-prompt` tells the
reviewer to use `git`.

A review can outlast the Bash tool's 10-minute cap, so the worker starts it
with `run_in_background` and waits for the completion notice. A `-p` session
stays alive while a background job runs and is re-prompted when it exits.

`evals/sandbox-probe`, `evals/sandbox-review-probe` and `evals/bg-wait-probe`
re-run those tests. Each calls the real `claude` and spends real money, from
about $0.30 an arm up to the budget each script passes; run them after a Claude
Code upgrade or before changing a flag.

## The driver

`scripts/epic-loop` assembles both calls. Run it from anywhere; the target repo
comes from `--repo`, or from the git root of the current directory.

```bash
epic-loop BEAD-ID [options]

  --hold               Stop each bead at ready-for-review; never merge
  --repo DIR           Target repository (default: git root of $PWD)
  --dry-run            Print the exact calls and exit; spends nothing
  --budget USD         Max API spend for the working call; reviews add their own
                       (default: 200.00)
  --review-budget USD  Max API spend for each review, on top of --budget
                       (default: 10.00)
  --max-turns N        Claude Code turn cap for the working call (default: 400)
  --turn-budget N      Parent's turn counter the goal stops at (default: 20)
  --model NAME         Model (default: claude-opus-5)
  --log-dir DIR        Run logs (default: ~/.local/state/epic-loop)
  --session-id UUID    Reuse a session id instead of generating one
```

It takes any bead with children -- an epic, a feature, a task with subtasks.
What matters is that there are children to work, not what the parent is called.

Before spending anything it refuses a bead that does not exist, is closed, has
no children, or whose children are all settled. It refuses to run from a linked
worktree, since the skill creates worktrees under the main checkout and must
not nest them. It checks that `claude`, `bd`, `gh`, `jq`, `git` and `uuidgen`
are all present, and that `claude` is 2.1.272 or newer.

It logs each run and prints the resume command when a cap stops it. Exit status
is the status of the working call; nonzero usually means a cap, not a fault. A
failed arming call exits 1 before the working call starts.

### bd's JSON shapes

`bd` returns a bare object, a single-element array, or -- since 1.2, which
stamps `schema_version` -- a `{"data": ..., "schema_version": N}` envelope
around either. A failure is a third shape: `{"error": ..., "schema_version": N}`
with no `data` key at all. The driver's unwrapper requires both keys before it
takes `.data`, so an error object survives intact and stays readable.

## The test

`scripts/epic-loop-test` proves the driver still assembles both calls
correctly. It stubs `claude`, so it spends nothing and touches no repository,
and it cleans up the throwaway beads it creates in the target tracker.

```bash
epic-loop-test                          # against the current repo
epic-loop-test --repo ~/code/otherproj  # against another beads workspace
epic-loop-test --driver ./scripts/epic-loop
epic-loop-test --keep                   # leave the fixtures for inspection
```

Run it after editing the driver. It refuses to start unless `claude` resolves
to its own stub, since a shadowed stub would run the real thing against a real
repository with `bypassPermissions`.

`evals/` asks the larger question the unit test cannot: given this SKILL.md,
does a session launch a run or start working beads itself? It runs the skill
against a throwaway repo with stubbed `claude` and `gh`, optionally alongside
an older copy of the skill, and grades both from what they left behind.
`evals/run-comparison --smoke` checks the harness without spending anything.
See `evals/README.md`, especially the note on why the sandbox has to be a repo
the per-bead protocol could actually run in.
