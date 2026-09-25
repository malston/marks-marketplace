---
name: epic-loop
description: Work every open child of a beads epic unattended. Type /epic-loop EPIC-ID in any Claude Code session that has bd, gh, git and claude available. It checks the epic, starts the run in the background, and hands back a log path and a resume command. Nothing to install first and no setup to understand. The run gives each bead its own worktree, branch and PR, writes a failing test first with the guard mutated to prove it bites, reviews in a fresh context, fixes serious findings and files the rest to a sibling findings epic, then merges the PR (or holds it for approval with --hold) and closes the bead before the next one starts. Design and keep-or-delete questions get a recommendation and a `human` tag instead of a decision. Takes --hold, --repo DIR, --review-budget USD and --dry-run. Not for a single bead, an epic with no children, or work that needs a human decision at every step.
argument-hint: <epic-id> [--hold] [--repo DIR] [--review-budget USD] [--dry-run]
compatibility: >-
  Needs the beads issue tracker (bd) and a repository whose work is tracked as
  beads with parent/child links, plus git, gh, jq, uuidgen and the claude CLI.
  Everything else it finds for itself.
disable-model-invocation: true
---

# Epic loop

Work the open children of a beads epic, one at a time, until every one is closed, blocked on a held PR, or tagged `human`.

## Which half of this file you are in

Read `$ARGUMENTS` before anything else. The bead id is the first word that is neither a flag nor a flag's value (the dollar amount after `--review-budget` is a value), and it can appear anywhere in the line.

- **`--worker` is present.** You are the run. Skip to [Working the run](#working-the-run) and follow it to the end. Everything in the next section is for a session that has not started yet.
- **`--worker` is absent.** Someone typed this in their own session. You are starting a run, not working beads. Follow [Starting a run](#starting-a-run) and stop there.

The distinction matters because the two jobs look alike and the failure is expensive: a session that mistakes itself for the launcher spawns a run that spawns a run.

## Starting a run

The whole job is to check the epic, launch the driver in the background, and report where it went. Four steps, no questions.

1. **Find the driver.** It is `scripts/epic-loop` under this skill's base directory, named at the top of this invocation. Use that absolute path. `epic-loop` on `PATH` is the same file when it is there, but do not depend on it.

2. **Check the plan.** Run the driver with `--dry-run` and everything the user gave you except the bead id:

   ```bash
   "$DRIVER" <bead> --dry-run [their other flags]
   ```

   Pass their flags through untouched rather than deciding which ones you recognize. `--hold`, `--repo`, `--budget`, `--review-budget`, `--model`, `--max-turns`, `--turn-budget` and `--log-dir` all belong to the driver.

   A dry run spends nothing. It refuses, with a message that names the fix, a bead that does not exist, is closed, has no children or whose children are all settled, and it refuses a linked worktree or a missing dependency.

   If it fails with **"no such bead"**, `bd` is scoped to a repository and you are standing in the wrong one. Ask which repository holds it, then retry with `--repo DIR`. Do not go looking for it.

   On any other failure, relay the driver's message as it stands and stop. It is written for a person.

   If the user passed `--dry-run` themselves, this step is the whole job. Show them the plan, say nothing was spent, and stop.

3. **Launch it.** Start the driver **in the background** with the user's flags. Background matters: the run outlives your turn, and a foreground call would tie up the session for hours and die with it.

   ```bash
   "$DRIVER" <bead> [their other flags]
   ```

4. **Report and stop.** The driver prints the repo, bead, mode, session, budget and log path before its first `claude` call, so give it a couple of seconds and read the background job's output back. If those lines are an error instead, the run did not start: pass the error on and stop. Otherwise say plainly which mode it is in, because merge mode merges PRs into `main` without asking again:

   ```text
   coderay-q2r -- epic, 7 children needing work
   repo:    ~/code/coderay
   mode:    merge (each PR lands on main once its review passes)
   budget:  $200, stops at 20 epic turns
   log:     ~/.local/state/epic-loop/20260912T220114Z-coderay-q2r.log
   resume:  claude --resume 3f2a...
   ```

   Then stop. Do not work beads yourself, and do not poll the log. The run is a separate session; you will be told when it exits.

If the driver is missing, unrunnable, or you cannot establish which repository is meant, say so and stop. Never fall back to working the beads in this session: this session has no `/goal` driving it, no turn budget, and it will stop after the first bead with the epic half finished.

The two `claude` calls behind the driver, the arming of `/goal`, the API key it strips and why, and the full option list are in `references/how-the-run-works.md`. Read it only if the driver misbehaves or you are changing it.

## Working the run

Everything below here runs in the session the driver started. `EPIC` is the first word of `$ARGUMENTS`; `HOLD` is true if `--hold` appears; `REVIEW_BUDGET` is the number after `--review-budget`, or 10 if it is absent.

Run `bd show $EPIC` first. Its DESIGN field may carry epic-specific instructions, most often the order to work the children in and which beads pair into one PR. Follow those. If DESIGN carries a full loop protocol, that protocol wins over anything below.

### The turn counter

A `/goal` re-evaluates the completion condition after every turn and survives a resumed session. The counter it stops at lives in the epic so a resumed session does not reset it.

The counter is a label, not a line in the notes. End every turn, whatever else happened in it, with one call:

```bash
bd update $EPIC --add-label turns-<N> --remove-label turns-<N-1>
```

Read it back from `bd show $EPIC --json` as the highest `turns-*` label, tolerating two: a turn that died between the add and the remove leaves both, and the run continues on the higher one rather than stopping.

The counter is a label so that keeping it cannot touch the notes field. Notes is a single shared prose field where a user keeps their own remarks, and a read-modify-write on it, performed once per turn by a model, gets performed as a plain overwrite eventually: one run wrote `bd update $EPIC --notes "turns: 5"` outright. `--add-label` cannot reach notes, so that mistake is not available. Never write the counter into notes, and never use `--notes` on the epic at all: the only safe write to that field is `--append-notes`.

If no goal is active, keep going anyway. End each turn by picking up the next bead, and stop only at the stop condition at the bottom of this file.

### Paths

`ROOT` is the main checkout, `git rev-parse --show-toplevel` run from where the session started. Worktrees live at `$ROOT/.claude/worktrees/<bead-id>`, always as absolute paths so a worktree is never created inside another. A review's throwaway clone lives at `${TMPDIR:-/tmp}/epic-loop/review-<n>-<tag>`, outside `$ROOT`. The main checkout belongs to the user. Never switch its branch, and never run a bare `git stash` (the stash stack is shared across worktrees).

### Findings epic

Review findings you don't fix go under a sibling epic, never under `$EPIC`. On the first filing of a run, look for an open epic titled `$EPIC review findings` with `bd list --type=epic`. If none exists, create it (`bd create "$EPIC review findings" --type epic`) and record its id in the PR body. Every finding filed there names the PR it came from in its description.

### Per bead

1. **Pick and isolate.** From `$ROOT`, `git fetch origin`. List open PRs from this loop (`gh pr list --label epic-loop --json number,headRefName,files`). For each held PR whose bead is blocked, check `gh pr view <n> --json state`. If it merged, remove its worktree and branch as in step 7 and `bd close` its bead with the PR number. Then pick the next open bead whose files don't overlap any still-open PR from this loop. If every remaining bead overlaps an open PR, report which PRs need to land and [stop early](#stopping-early). Never base a worktree on another PR's branch. Create the worktree with `git worktree add --no-track -b <branch> $ROOT/.claude/worktrees/<bead-id> origin/main` (`--no-track` so `git push -u origin <branch>` works). If `git worktree list` already shows one for this bead, reuse it. `cd` into it, `uv sync --locked`, and run steps 2 to 6 from there.

2. **Claim and scope.** `bd update <id> --claim`. Re-read the bead. If an earlier PR already covered part of it, don't edit the bead's title or description. Write down exactly what you're dropping and why, and carry that into the PR body's "Trimmed" section and the bead's close reason. Batch beads that share a file into one PR and say so in the body.

3. **Test first.** Write the failing test, watch it fail for the right reason, make the smallest fix, then mutate the guard both ways and watch the test go red each time before restoring it. After a mutation round, `rm -rf src/**/__pycache__` before trusting the suite. A same-size restore in the same second leaves a stale `.pyc` and the suite passes against the mutated code. Run the full suite (`uv run pytest tests/ -q`, the same command as `make test`). Gate every commit with `&&` on a pytest grep, since `set -e` doesn't abort in this tool. Edit files with Python, not `sed -i`.

4. **Open the PR.** `git push -u origin <branch>`, then `gh pr create --label epic-loop` with these sections: what changed, trimmed (what was dropped from the bead and why, or "nothing"), decisions left for the user, tests (red and green counts, mutations), verified by hand, what stays as is. Wait for CI in two steps. `gh pr checks <n> --watch` on its own returns at once before CI has registered the run, so first poll until the check exists (`until gh pr checks <n> | grep -q pytest; do sleep 10; done`), then `gh pr checks <n> --watch`.

5. **Review in a fresh process, from a sandboxed clone.** Each review runs as its own `claude -p` process started inside a throwaway clone of the repository. It starts in the clone, so it has no working directory to drift from, and the clone has its own HEAD, branches and index, so a checkout there cannot move `$ROOT` or the bead's worktree. The strict sandbox stops its Bash commands, and those of any subagent it starts, from writing outside the clone and the session temp directory, including a retry with the sandbox disabled. The sandbox covers only Bash, so the edit tools are denied, MCP servers are not loaded, and project settings (and so the PR branch's own hooks) are skipped. Run one review at a time, each in its own clone, and treat `<tag>` as the review's name (`code-review`, `review-pr`). Every block below is its own Bash call, and a shell variable does not survive from one call to the next, so each block sets `C` itself.
   - **Before each review.** Record, for `$ROOT` and for the bead's worktree, `git -C <dir> rev-parse HEAD`, `git -C <dir> symbolic-ref -q --short HEAD || echo '(detached)'` and `git -C <dir> branch --format='%(refname:short)'`, plus `git -C <bead's worktree> status --porcelain`. `$ROOT`'s uncommitted files stay out of the comparison, since the user may be editing there, so say so in the review round rather than relying on it. Then build the clone:

     ```bash
     C="${TMPDIR:-/tmp}/epic-loop/review-<n>-<tag>"
     rm -rf "$C" "$C.json"
     git clone -q --shared "$ROOT" "$C" &&
     git -C "$C" remote set-url origin "$(git -C "$ROOT" remote get-url origin)" &&
     git -C "$C" fetch -q origin main <branch> &&
     git -C "$C" checkout -q --detach origin/<branch> &&
     git -C "$C" branch -f --no-track main origin/main
     ```

     The detached HEAD and the reset `main` matter: `/code-review` diffs `@{upstream}...HEAD`, falling back to `main...HEAD`, so `main` must be the current `origin/main`. If the block fails, run it again once from the top, which rebuilds the clone. If it fails again, remove the clone (see **Giving up** below), report it and pick up the next bead, leaving this one claimed.
   - **Run.** From the clone, with nothing from this session in the prompt:

     ```bash
     C="${TMPDIR:-/tmp}/epic-loop/review-<n>-<tag>"
     (cd "${C:?}" && claude -p "/code-review medium <n>" \
         --settings '{"sandbox":{"enabled":true,"allowUnsandboxedCommands":false,"failIfUnavailable":true}}' \
         --setting-sources user --strict-mcp-config \
         --disallowedTools "Edit,Write,NotebookEdit" \
         --append-system-prompt "PR <n> is checked out as HEAD and main is its base. Use git, not gh: gh cannot reach GitHub from this sandbox." \
         --permission-mode bypassPermissions \
         --max-budget-usd <REVIEW_BUDGET> --output-format json </dev/null >"$C.json")
     ```

     Start it with `run_in_background`, because a review can outlast the Bash tool's 10-minute cap. A turn can end while it runs, and the session is prompted again when the job exits; until then, keep waiting for this review rather than starting other work, and never start a second copy while the first is running.

     The sentence goes in `--append-system-prompt` and not in the prompt, because everything after the slash command becomes that command's arguments. The sandbox blocks `gh` on macOS because Go tools need the system TLS trust service. `sandbox.enableWeakerNetworkIsolation` would open it, but it also opens an exfiltration path, and the reviewer gets everything it needs from `git`. `--strict-mcp-config` with no `--mcp-config` loads no MCP servers, since MCP tools run outside the sandbox and bypass mode would let a reviewer push, merge or send through them unasked.

     The review is `jq -r .result` of `$C.json`. If its `.subtype` is not `success`, the review did not finish: rebuild the clone with the **Before** block and run it once more, and if that fails too, give up on the review as below. If the PR carries a bead of priority P0, P1, P2 or P3, repeat these bullets for `/pr-review-toolkit:review-pr <n>` with its own clone once the first review is back. A PR whose beads are all P4 stops at `/code-review`.
   - **After each review.** Run the recorded commands again. If any value differs, [stop early](#stopping-early), naming the checkout and what changed and the clone's path, and leave both as they are. Otherwise remove the clone:

     ```bash
     C="${TMPDIR:-/tmp}/epic-loop/review-<n>-<tag>"
     rm -rf "${C:?}" "$C.json"
     ```

     Stay in the bead's worktree until the bead's fixes are pushed.
   - **Giving up.** A review abandoned after its second failure leaves nothing behind: run the removal block above, then report the failure and pick up the next bead, leaving this one claimed.

6. **Fix or file.** Fix every finding the reviews label Critical, Important or HIGH, and any finding that is a correctness or security defect whatever its label, in one review commit. Re-run checks. Add a "Review round" section to the PR body. File everything else under the findings epic after `bd search` for a duplicate, P3 for behavioural, P4 for style or simplification, with "PR <n> review" in the description. Findings outside the bead's scope are filed, never fixed in this PR.

7. **Land or hold.**
   - Merge mode: `gh pr merge <n> --merge` (a merge commit, not a squash, so the branch tip stays reachable from `origin/main`). Back in `$ROOT`, `git fetch origin`. Once `git branch -r --contains <branch>` lists `origin/main`, `git worktree remove $ROOT/.claude/worktrees/<bead-id>` and `git branch -D <branch>`. The remote branch stays. `bd close <id> --reason="PR <n>: ..."` including any trim, then `bd show <id>` to confirm the status changed. Then the next bead.
   - Hold mode: `gh pr ready <n>` if it's a draft. `bd update <id> --status blocked --append-notes "held: PR <n>"`, which keeps whatever the notes already held. Leave the worktree and branch in place. Then the next non-overlapping bead. The cleanup and close happen in step 1 of a later pass once the PR has merged.

### Stopping early

A goal re-prompts a session that only says it has stopped, and the run carries on to the next bead. To stop before the epic is settled, take the number the goal condition itself names as the counter it stops at, which is not always 20, and make that the label:

```bash
bd update $EPIC --add-label turns-<cap> --remove-label turns-<N> \
               --append-notes "halted: <reason>"
```

That replaces the counter write [the turn counter](#the-turn-counter) asks for, for this turn only. `--append-notes` adds the reason on its own line and keeps whatever the notes already held. Then report the reason and what a person has to look at, and end the turn.

Say in the report that a later run needs the `halted:` line removed and the `turns-<cap>` label replaced with the real count, since the goal otherwise reads the epic as finished the moment it starts.

### Decision beads

A bead that asks whether to keep or delete code, or that has an open design question, isn't yours to decide. Investigate, write the recommendation with `bd update <id> --append-notes`, run `bd tag <id> human` (listed by `bd human list`; `bd human <id>` on its own only prints a help menu), and move on. Never delete code that seems unused or rewrite an implementation without the user.

### Never

- Edit a bead's title or description. Trims go in the PR body and close reason.
- Write a notes field with `--notes`. Add to it with `--append-notes`, which keeps what is there.
- Base a worktree on another PR's branch.
- File a finding under `$EPIC`.
- Review a diff from the session that wrote it.
- Run a review anywhere but its own sandboxed clone.
- Merge in hold mode.
- Bump the version, tag, or cut a release.

### Stop

When every child of `$EPIC` is closed, blocked on a held PR, or tagged `human`, report the state in a few lines. Name the findings epic id and how many beads it holds, and in hold mode list the PRs waiting for approval. Then stop.
