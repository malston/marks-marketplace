---
name: backlog-groom
description: Work through a beads backlog with the user, one bead at a time, bringing each up to the definition of ready. Type /backlog-groom to groom everything open, or /backlog-groom EPIC-ID for one epic's children. It rewrites acceptance criteria, splits oversized beads, adds missing dependency edges and tags decisions for a human, asking before each change. Use it when the backlog has drifted or before handing an epic to a worker loop. Not for bulk filing; use plan-to-beads for that.
argument-hint: [epic-id] [--repo DIR] [--limit N]
---

# Backlog groom

A conversation, not a batch job. Each bead gets shown, judged against the bar,
and changed only after the user agrees. That is why this runs in the main
session: a subagent cannot ask what a half-written bead was supposed to mean,
so it either guesses or gives up, and both are worse than asking.

## Setup

Read `$ARGUMENTS`. An epic id, if present, scopes the session to its children.
Otherwise groom every open bead, oldest first.

Repository from `--repo` or the git root. Read
`.claude/definition-of-ready.md`; it is the bar for this session. Run `bd prime`
for the command surface.

`--limit N` stops after N beads. Default to 10 and say so. Grooming is
attention-bound and a session that runs to forty beads gets rubber-stamped
somewhere around fifteen.

Go through beads in the order the scope gives you -- oldest first, or an
epic's own child order -- and do not skip ahead to one that looks more
interesting, an oversized bead begging to be split, say. The order is a
promise that nothing gets passed over, and jumping the queue breaks that
promise for every bead between where you were and where you jumped to.

The limit counts beads reached, not beads rewritten. A bead you split is one
stop against the count, not zero, and the children a split produces are not
extra stops to spend the rest of the budget on. When you hit the limit, stop
there, even mid-bead, rather than let one expensive change consume the beads
behind it.

## The loop

For each bead: show it, judge it, propose one change, apply it or move on.

**Show** the title, description, acceptance criteria, edges in and out, age,
and status. Compact. The user wrote most of this and does not need it read
back at length.

**Judge** it against the definition of ready and name the clause it fails.
Failing clause 4 is a different problem from failing clause 2 and has a
different fix, so be specific.

**Propose** the change as a concrete rewrite, not a description of one. Show
the acceptance criteria you would write. Show the two beads you would split it
into. A proposal the user can accept with one word moves faster than a question
they have to answer in a paragraph.

**Apply** after agreement, then move on. If the user wants to think about it,
leave the bead alone and note it at the end.

Do not batch changes to the end of the session. A batch gets approved as a
block and the individual judgements stop happening.

## What each failure looks like

**No named files.** Ask which package. If the user does not know either, the
bead is really a spike, so retitle it as one and give it a time box.

**Two outcomes in one bead.** Propose the split with an edge between the halves
if one genuinely blocks the other, and no edge if they are independent. Say
which you chose and why.

**No test described.** Ask what would convince them it works. That answer is
the acceptance criterion, usually close to verbatim.

**A decision.** Do not rewrite it into a task. Investigate enough to make a
recommendation, write the recommendation into the notes, tag it `human`, move
on. Never decide it yourself, and never decide it by rewriting the bead into
something that implies the decision was already made. The tag itself costs one
call and nothing else, so apply it the moment you reach the bead rather than
leaving it for a later pass that a tight limit may not reach.

**Dependency in prose.** Add the edge. Leave the sentence alone; it is
readable and now it is also scheduled.

**Stale.** Open a long time, untouched. Ask whether it is still real. If the
answer is no, closing is the user's call and they should make it.

## Notes fields

Read, change your line, write the whole field back. The notes field is one
string and the user keeps their own remarks in it, so a write that carries only
your line destroys theirs. This is the same rule the worker loop follows for
its turn counter, for the same reason.

## Never

- Change a bead without the user agreeing to that specific change.
- Close a bead. Propose it; they close it.
- Set priority. Rank by dependency depth and by how many beads unblock, present
  that as a proposal, and let them decide what ships first. You do not know the
  calendar.
- Resolve a design question that was filed as a decision.
- Run `bd cleanup` or `bd compact`. Grooming needs the history those remove.

## End

Report in a few lines: how many beads were seen, how many changed, how many are
now ready, how many are tagged `human`, and which ones were left for later.
Then stop.
