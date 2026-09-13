# beads-pm

The product-manager half of a beads workflow. `epic-loop` works an epic's
children; this fills the epic and keeps it worth working.

```sh
plan document
    |
    v
/plan-to-beads        decompose, agree the shape, file          (skill + filer agent)
    |
    v
/backlog-audit        check the graph before spending anything  (skill + auditor agent)
    |
    v
/backlog-groom        fix what the audit found                  (skill)
    |
    v
/epic-loop EPIC-ID    work every child unattended               (separate plugin)
```

## Install

```bash
claude plugin marketplace add malston/marks-marketplace
claude plugin install beads-pm@marks-marketplace
```

Then, in each repo you use it in:

```bash
bd init                       # if you have not
~/.claude/plugins/beads-pm/scripts/bd-pm-init
$EDITOR .claude/definition-of-ready.md
```

That last step is not optional. The definition of ready is the bar all three
skills and both agents judge against, and the template ships with the
project-specific section blank.

## Why it is split this way

Subagents cannot ask a question mid-run. They get a prompt, work in their own
context, and return one result. That makes them right for work that reads a
lot and returns a little, and wrong for anything where the answer depends on
something only a person knows.

So the batch work lives in `agents/`: filing an agreed decomposition, reading
a whole graph to find its faults. The decisions live in `skills/`, in the main
session, where the user is.

## Why the definition of ready lives in the repo

Half of it is project-specific. The test command, the layout, what counts as a
reasonable slice. A copy inside the plugin would be generic, and it would also
be invisible to `epic-loop`, which runs from a different plugin and needs the
same bar when it decides whether to claim a bead.

`.claude/definition-of-ready.md` is shared ground. Edit it and the filer, the
auditor, the grooming session and the worker loop all change together.

Not `.beads/`. That directory is the Dolt database `bd` manages, and a markdown
file dropped in beside it is one `bd doctor` run away from being moved or
removed. `.claude/` is already where `epic-loop` puts its worktrees, so both
plugins are reading from a directory that belongs to the agents.

## Command surface

Nothing here hardcodes `bd` flags beyond the handful that have been stable.
Every skill and agent runs `bd prime` first and takes syntax from there. Beads
moves fast, and a frozen command reference in a prompt is a bug with a delay
on it.

## Handoff to epic-loop

`epic-loop` claims a bead and gives it a worktree, a failing test, a pull
request and a review pass. It works best on a bead that names its files and
describes its test, which is exactly what the definition of ready asks for.

Two things to wire up on the `epic-loop` side if you want the contract to
hold both ways:

1. Have it read `.claude/definition-of-ready.md` in step 2, after it claims and
   re-reads the bead. A bead that fails gets tagged `human` instead of worked,
   which turns a wasted session into a one-line report.
2. Have it file review findings through the same bar. Findings filed to the
   sibling epic are beads a later loop will claim, so they need named files and
   a described test like anything else.
