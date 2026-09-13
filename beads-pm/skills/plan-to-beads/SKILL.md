---
name: plan-to-beads
description: Turn an approved plan document into a beads epic with children and dependency edges. Type /plan-to-beads with a path to the plan, or point it at one already in the conversation. It decomposes the plan, shows you the graph shape before anything is written, and only files once you agree. Filing itself runs in a subagent so the tool output never enters this session. Use it after a plan has been revised and settled, not to write the plan. Takes --repo DIR and --epic TITLE.
argument-hint: <plan-path> [--repo DIR] [--epic TITLE]
---

# Plan to beads

A settled plan becomes an epic with children and edges. The expensive mistake
here is filing forty beads and finding out afterwards that the decomposition
was wrong, so the shape gets agreed before anything is written.

## Setup

Read `$ARGUMENTS`. The plan path is the first word that is not a flag. If no
path is given, use the plan already in this conversation; if there is none,
ask for it and stop.

Work out the repository from `--repo`, or from the git root of the current
directory. Confirm `.beads/` exists there. If it does not, `bd init` has not
been run and there is nothing to file into.

Read `.claude/definition-of-ready.md`. Every child you propose has to pass it.
If the file is absent, run `scripts/bd-pm-init` from this plugin's directory
and ask the user to fill in the project specifics before going further. Filing
against an unfilled template produces acceptance criteria naming a test command
that does not exist here.

Run `bd prime` for the current command surface. Take syntax from there.

## Decompose

Read the plan. Produce a tree in this session, in your own context, before any
subagent is involved.

For each child, write the title, the files it touches, the outcome, the test
that proves it, and which other children it waits on. That last one is the part
that determines whether any of this works, so give it most of the effort.

Two things to get right while you are still cheap to correct:

**Slice along the grain of the code.** A child that touches one package is a
child a worker can finish. A child defined by a user-visible feature usually
touches four packages and dies halfway through a session.

**Make the edges real.** An edge means the second bead genuinely cannot start
until the first lands, usually because it imports something the first creates
or changes a file the first rewrites. An edge added because the work feels
sequential serialises the whole epic for no reason. An edge left out because
the dependency felt obvious hands a worker a bead it cannot do.

## Show the shape, then stop

Before filing, show the user the tree and these numbers:

```
epic:      <title>
children:  <n>
edges:     <n>
depth:     <n levels>
ready now: <n> of <n>
human:     <n> decisions
```

Read `ready now` out loud to yourself. If most children are ready at the start,
the decomposition came out flat and the graph carries no ordering information.
Say so and propose the edges you think are missing. Flatness is the usual
failure of this step and it is invisible once the beads exist.

Ask for approval. Take corrections, redraw, ask again. Iterate here as long as
the user wants, since nothing has been written yet and each pass costs one
turn.

## File

On approval, dispatch the `backlog-filer` subagent. Hand it the epic title, the
full child list with descriptions and acceptance criteria, the edge list, and
the repo path. It files what it is given and returns a short report.

Filing goes to a subagent because creating forty beads generates pages of tool
output that this session never needs and cannot afford to hold. The decisions
were all made above; what is left is typing.

Relay its report. If it lists children it refused to file, work those with the
user now rather than leaving them for a later pass, because a child missing
from the epic is one a worker loop will never notice is absent.

## Then audit

Dispatch `backlog-auditor` against the new epic. It reads the graph fresh and
catches what the filer's own view of its work cannot: a cycle that only appears
once every edge exists, a child that duplicates something already in the
backlog from an earlier plan.

Report its findings and stop. Do not start working the beads.

## Never

* File before the user has seen the shape.
* Let the filer decide scope. It writes what it is handed.
* Write acceptance criteria that assume the reader has seen the plan. The
  worker will not have.
* Set priority fields on the user's behalf. Propose an order and let them say.
