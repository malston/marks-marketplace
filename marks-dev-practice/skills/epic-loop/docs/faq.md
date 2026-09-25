# Epic Loop FAQ

Questions an engineer tends to ask before, during and after a run. The
[README](../README.md) covers what the skill does;
[how-the-run-works.md](../references/how-the-run-works.md) covers the
plumbing.

- [Getting started](#getting-started)
- [During a run](#during-a-run)
- [Merge mode and hold mode](#merge-mode-and-hold-mode)
- [Beads bookkeeping](#beads-bookkeeping)
- [Reviews](#reviews)
- [Costs and limits](#costs-and-limits)
- [Safety](#safety)
- [Troubleshooting](#troubleshooting)
- [Changing the skill](#changing-the-skill)
- [What does arming a goal mean?](#what-does-arming-a-goal-mean)

## Getting started

### What do I need installed?

`claude` 2.1.272 or newer, `bd`, `gh`, `git`, `jq` and `uuidgen`, and a
repository tracked with beads whose epic has parent/child links to its work.
The driver checks all of this before it spends anything.

### Does the parent have to be an epic?

No. Any bead with children works: an epic, a feature, or a task with subtasks.
What matters is that it has open children to work.

### Does it work on a project that isn't Python?

Not as written. The per-bead protocol in `SKILL.md` runs `uv sync --locked`,
runs the suite with `uv run pytest tests/ -q`, and waits for a CI check named
`pytest`. For another stack, write the protocol you want into the epic's
DESIGN field. The worker reads DESIGN first, and a full loop protocol there
wins over the one in `SKILL.md`. DESIGN is also where to put the order to work
the children in, and which beads should share one PR.

### How do I see what it will do without spending anything?

`/epic-loop <epic-id> --dry-run`. It checks the epic, names how many children
need work, and prints the exact two `claude` calls it would make.

### Where do I run it from?

From a Claude Code session in the repository's main checkout. The driver
refuses to run from a linked worktree, because it creates worktrees under the
main checkout and must not nest them. To work an epic in another repository,
pass `--repo DIR`.

### What order does it work the beads in?

The order in the epic's DESIGN field if there is one. Otherwise it picks the
next open bead whose files don't overlap a PR this loop still has open, and
skips any that do.

## During a run

### Can I close the session I started it from?

Yes, from 0.9.1 on. The launcher starts the driver under `nohup`, so the driver
belongs to `launchd`, not to your session. Closing the session doesn't stop the
run. In 0.9.0 and earlier the driver was a background job of the launching
session, so keep that session open for runs started with those versions.

### How do I know when it's finished?

The log's last line reads `finished:` with the elapsed time and the exit
status. The launching session is not told, because the run is detached.

### Why does the log stop after the header?

The driver writes a header (repo, epic, session, goal, start time) and the
arming call's result, then starts the working session with `--output-format
text` and copies that session's output into the log. In practice little arrives
until the session ends. To see progress mid-run, look at what the run leaves
behind:

- the epic's `turns-N` label, which goes up at the end of every turn
- each child bead's status: `in_progress`, `blocked`, `closed`, or the `human`
  label
- PRs labeled `epic-loop` (`gh pr list --label epic-loop`)
- worktrees under `.claude/worktrees/`
- review clones under `${TMPDIR:-/tmp}/epic-loop/` while a review runs

The session's full transcript is also on disk; `claude --resume <session-id>`
opens it.

### How do I stop a run?

Kill the working session, not the driver: find it with
`pgrep -fl 'claude -p /epic-loop'` and `kill` that pid. The driver then writes
its `finished:` line with a nonzero exit status. The bead in progress stays
claimed (`in_progress`) and its worktree stays in place. `SKILL.md` doesn't say
how a later run treats a bead that is still `in_progress`, so set it back with
`bd update <bead-id> --status open` before the next run; step 1 then reuses its
worktree.

### How do I resume a run that stopped?

Type `/epic-loop <epic-id>` again. The turn counter lives on the epic, so it
carries on from where the last run stopped. Step 1 reuses a bead's existing
worktree, and cleans up any held PR that has merged in the meantime.

To continue the same session instead, use the resume command the banner
printed. `claude --resume <id>` opens it interactively. To keep it unattended,
run the driver with `--dry-run --session-id <old-id>` plus the run's other
flags, and run call 2 from its output. That call already strips the API key
variables and resumes the old session.

## Merge mode and hold mode

### What's the difference?

In merge mode, the default, each PR is merged into `main` as soon as its
review round passes, with nobody asked again. In hold mode (`--hold`), each PR
stops at ready-for-review, its bead is marked `blocked` with a `held: PR <n>`
note, and the run moves on to the next bead that doesn't overlap it.

### What happens to a held PR after I merge it?

The next run cleans it up in step 1: it removes the bead's worktree and local
branch and closes the bead with the PR number. You can also do that by hand:
`git worktree remove .claude/worktrees/<bead-id>`, `git branch -D <branch>`,
then `bd close <bead-id> --reason="PR <n>: ..."`.

### Why merge commits and not squash?

A merge commit keeps the branch tip reachable from `origin/main`. The run
checks `git branch -r --contains <branch>` for `origin/main` before it deletes
the local branch, and a squash merge would never pass that check.

### Why did the run stop with beads still open?

Most often because every remaining bead touches files that an open PR from
this loop also touches. The run won't base one PR on another, so it stops early
and names the PRs that need to land first. A stop like that sets the epic's
counter to its limit and adds a `halted:` line to its notes, so merge the PRs,
remove the `halted:` line, set the `turns-*` label back to the real count, and
then run it again. Otherwise the next run reads the epic as finished before it
starts.

## Beads bookkeeping

### What is the findings epic?

A sibling epic titled `<epic> review findings`. Review findings the run doesn't
fix go there, each naming the PR it came from, at P3 for a behavior problem or
P4 for style. It is never a child of the epic being worked, so filing findings
can't keep the run going forever.

### What does the `human` tag mean, and how do I hand a bead back?

The run tagged the bead because it asks a design or keep-or-delete question.
The worker's investigation and recommendation are in the bead's notes; read
them with `bd show <bead-id>`. To hand it back, record your decision and remove
the tag:

```bash
bd update <bead-id> --append-notes "Decided: <your decision>" --remove-label human
```

The next run works it, and finds your decision in the notes.

### Why is the turn counter a label and not a line in the notes?

Notes is one shared prose field where you keep your own remarks. Updating a
counter in it means a read-modify-write every turn, and a model eventually
does that as a plain overwrite: one run wrote `bd update <epic> --notes "turns: 5"`
and wiped the notes. Adding and removing a label can't touch the notes.

### There's an old `turns: N` line in my epic's notes. Is it safe to delete?

Yes. Earlier runs kept the counter in the notes. The current counter is the
highest `turns-*` label, and the notes line is ignored.

### The run stopped at the turn limit. How do I restart it?

Raise the limit with `--turn-budget`, or reset the counter label to a lower
number. If the run stopped early on purpose, the epic also has a `halted:`
line in its notes and a `turns-<cap>` label; remove the line and set the label
back to the real count, or the next run reads the epic as finished before it
starts.

## Reviews

### Which reviews run?

`/code-review medium` on every PR. `/pr-review-toolkit:review-pr` as well if
any bead in the PR is P0, P1, P2 or P3. A PR whose beads are all P4 gets only
the first.

### Why does each review run in its own process, in a clone?

A review used to run as a subagent of the worker, in whatever directory the
worker was in. That directory drifts back to the main checkout on its own, and
`/code-review` checked out a PR branch there. A separate `claude -p` process
started inside a throwaway clone has no directory to drift from, and a
checkout inside the clone moves only the clone. It also can't see anything
from the session that wrote the diff.

### What can't a reviewer do?

- Write outside its clone and the session temp directory with Bash, including
  by retrying a command with the sandbox turned off
- Use Edit, Write or NotebookEdit
- Use any MCP tool: none are loaded
- Run hooks committed on the PR branch: project settings are skipped
- Reach GitHub with `gh`, on macOS
- Spend more than `--review-budget`

`references/how-the-run-works.md` explains the gap each setting closes, and the
probe scripts in `evals/` re-run the tests behind them.

### Why can't the reviewer use `gh`?

On macOS, Go tools like `gh` need the system TLS trust service, and the sandbox
blocks it, so `gh` fails with `x509: OSStatus -26276`. The setting that would
open it also opens a path to send data out, so it stays off. The worker checks
the PR branch out in the clone before the review starts, and the reviewer reads
everything from `git`.

### What happens to the findings?

Critical, Important and HIGH findings, and any correctness or security defect,
are fixed in one review commit on the PR, and the PR body gets a "Review round"
section. Everything else is filed under the findings epic. A finding outside
the bead's scope is always filed, never fixed in that PR.

### What if a review fails?

The worker rebuilds the clone and runs the review once more. If it fails
again, the clone is removed, the failure is reported, and the run moves to the
next bead, leaving this one claimed.

### Why does the worker wait on a review with Monitor?

A review can take longer than the Bash tool's 10-minute limit, so it runs as a
background job. A `claude -p` session exits when its turn ends unless a monitor
is still running, and it kills its background jobs when it goes. The first run
of the sandboxed review ended its turn to wait, and the review died 30 seconds
in. So the command that starts the reviewer writes a `.done` file when the
reviewer exits, and the worker watches for that file with Monitor.

## Costs and limits

### What does a run cost?

There are three limits, and they are separate:

| Limit             | Default | Covers                                            |
| ----------------- | ------- | ------------------------------------------------- |
| `--budget`        | $200    | The working session and its subagents, in dollars |
| `--review-budget` | $10     | Each review, on top of `--budget`                 |
| `--turn-budget`   | 20      | Epic turns, counted by the `turns-N` label        |

Claude Code's own `--max-turns` (400) is a fourth, a stop for a session that
has gone wrong.

Reviews on real coderay beads cost between $0.44 and $1.45 each, $1.06 to
$1.89 for both reviews on one bead. With two reviews, each retried once, a bead
can spend up to four times `--review-budget` on reviews.

### Why did a run bill my API account instead of my subscription?

A key in `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` outranks the claude.ai
login. The driver removes both from its calls, so a key exported by a direnv
`.envrc` or your shell doesn't move the run onto a pay-as-you-go account. Set
`EPIC_LOOP_KEEP_API_KEY=1` when that account is the one you mean to spend. If
you type the calls by hand, prefix them with
`env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN`.

## Safety

### Will it touch my main checkout?

It never switches your checkout's branch and never runs a bare `git stash`.
Before and after each review it records the HEAD, branch and branch list of
your checkout and the bead's worktree, and stops the run if any of them
changed. Your uncommitted files are left out of that check, because you may be
editing while the run works.

### Is the working session sandboxed?

No. Only the reviewers are. The working session runs with
`--permission-mode bypassPermissions` so it can work without anyone there to
approve its commands, and it has the access you have in that repository. The
rules it follows are in `SKILL.md`; the ones it must never break are under
"Never".

### What will it never do?

Edit a bead's title or description, overwrite a notes field, base a worktree
on another PR's branch, file a finding under the epic being worked, review a
diff from the session that wrote it, run a review outside its sandboxed clone,
merge in hold mode, or bump a version, tag or cut a release.

## Troubleshooting

### "no such bead"

`bd` looks up beads in the repository you're standing in. Run from the
repository that holds the epic, or pass `--repo DIR`.

### "claude X is too old"

Upgrade Claude Code to 2.1.272 or newer. Older versions let `/goal` stop
checking its condition after an API error or a dropped connection, and the run
then ends with the epic half done, reading as a clean finish.

### "the goal-arming call failed"

The first `claude` call didn't come back healthy, most often because of
authentication or credit. The message and the full result are in the log.
Nothing was worked.

### It refuses to run from a worktree

Run it from the main checkout. The driver creates worktrees under the main
checkout and refuses to nest them.

## Changing the skill

### How do I test a change?

- `scripts/epic-loop-test --repo <dir>` tests the driver with `claude` stubbed.
  It needs a beads workspace; a throwaway one works: `git init`, an empty
  commit, then `bd init --non-interactive --stealth`.
- `evals/run-comparison --smoke` checks the eval harness and a stubbed driver
  run, and spends nothing.
- `evals/run-comparison` runs the launcher end to end in a sealed sandbox, for
  about $2.
- `evals/sandbox-probe`, `evals/sandbox-review-probe` and `evals/bg-wait-probe`
  check the review sandbox and the Monitor wait against the real `claude`. Run
  them after a Claude Code upgrade or before changing a review flag.

### How do I try a branch against a real repository without installing it?

Point `CLAUDE_CODE_PLUGIN_DIRS` at a checkout of the branch's
`marks-dev-practice` folder and run that checkout's driver:

```bash
CLAUDE_CODE_PLUGIN_DIRS=~/path/to/checkout/marks-dev-practice \
  ~/path/to/checkout/marks-dev-practice/skills/epic-loop/scripts/epic-loop <epic> --hold
```

The variable loads the plugin from that folder for every `claude` process the
run starts, and replaces the installed copy for those sessions. It needs Claude
Code 2.1.280 or newer.

### What is `scripts/label-findings`?

A measurement tool, not part of the loop. It asks a model to label every
finding the loop has filed as a real defect, low value or a false positive,
and prints each label next to what actually happened to the finding. It reads
beads and never changes them. Use `--dry-run` to see the request without
spending anything.

## What does arming a goal mean?

Arming a goal means attaching a finish line to a Claude session before the
work starts. It's the first of the two `claude` calls the driver makes, and
it's what lets one session keep going through a whole epic unattended.

### What `/goal` does

`/goal <condition>` is a Claude Code command that stores a completion
condition on the session. After **every turn**, Claude Code checks that
condition. If it isn't met, the model is prompted again to keep working
instead of stopping. The condition is saved with the session, so it still
applies when the session is resumed.

For epic-loop, the condition is:

```text
Every open child of beads epic <id> is closed, blocked on a held PR, or tagged `human`,
worked per /epic-loop; or stop when the epic's turn counter reaches 20
```

Without it, a `claude -p` session does one piece of work, ends its turn and
exits. With it, finishing a bead ends the turn, the check fails because more
beads are left, and the session is sent back to pick up the next bead.

### The arming call

```bash
claude -p "/goal <condition>" --session-id "$SID" --max-turns 1 \
    --disallowedTools "Bash,Edit,Write,NotebookEdit,Task,Agent"
```

This call does nothing except record the goal on session `$SID`. Then the
second call resumes that same session with `/epic-loop <id> --worker`, and the
goal comes with it.

### Why it takes its own call

- **Only the first slash command in a prompt gets expanded.** Anything after it
  becomes that command's arguments. So `/goal` and `/epic-loop` can't go in the
  same prompt.
- **The model won't run either command on its own,** because the skill sets
  `disable-model-invocation: true`. Both have to be typed.
- **Tools off and one turn.** `/goal` tells the model to start working. If the
  arming call could edit files, it would start working beads before the loop's
  instructions had loaded. With the tools denied and a one-turn limit, its
  first attempt to use a tool uses up the turn. So a healthy arming call ends
  on `error_max_turns` and exits 1, and the driver reads the JSON result to
  tell that from a real failure such as an auth or credit error.

This is also why the launcher waits for `working epic:` before reporting
success. That line prints only after the arming call has come back healthy.

### The stopping points

- **The condition is met:** every child is closed, held, or tagged `human`.
  That's the normal end.
- **The turn counter reaches the limit.** The worker adds a `turns-N` label to
  the epic at the end of every turn, and the goal stops at 20 by default, set
  by `--turn-budget`. It's a label on the epic rather than something in memory,
  so resuming a session doesn't reset it, and a second run on the same epic
  carries on from the last run's count.
- **Stopping early on purpose:** the worker sets the label straight to the
  limit and adds a `halted:` note.

They are separate from Claude Code's own `--max-turns 400`, which stops a
session that has gone wrong, and from the dollar cap, `--budget`, which the
driver passes to Claude Code as `--max-budget-usd`.

### What we've actually seen

In the successful coderay runs, the counter went from `turns-1` to `turns-3`
inside **one** `claude -p` process, so the goal did send the session back
between beads. In the failed first attempt, though, the worker ended a turn
with only a background review job running, and the process exited with the
goal still unmet. There was no goal check at the end of that transcript. The
Monitor wait avoids that case. The documentation doesn't explain exactly when
`/goal` doesn't get to act, so treat it as a real limit of the tool rather than
something fully understood.

This mechanism requires Claude Code 2.1.272 or newer, which is when `/goal`
stopped stalling after API errors. The driver refuses to start on anything
older.
