---
name: backlog-audit
description: Check a beads epic or a whole backlog for faults before a worker loop runs against it. Type /backlog-audit EPIC-ID. Dispatches a subagent that reads the graph and reports cycles, edges onto closed beads, orphans, decisions filed as work, duplicates, oversized beads and anything failing the definition of ready. Reports only; fixes go through backlog-groom. Run it after filing an epic and before starting epic-loop.
argument-hint: [epic-id] [--repo DIR]
---

# Backlog audit

Read the graph, report the faults, change nothing. This exists as its own entry
point because the check that matters most is the one nobody runs by hand: a
worker loop against an epic with a dependency cycle in it will work the beads
outside the cycle, declare itself done, and leave the rest unreachable with no
error anywhere.

## Run it

Read `$ARGUMENTS` for an epic id and `--repo`. With no epic id, say that you
are about to audit the whole backlog and ask whether that was meant, since a
full audit on a large tracker is expensive and usually is not.

Confirm `.claude/definition-of-ready.md` exists in the target repo. Without it
the auditor has no bar and will fall back to generic opinions about issue
hygiene, which is not worth the tokens. Run `scripts/bd-pm-init` first if it is
missing.

Dispatch the `backlog-auditor` subagent with the epic id and the repo path.
Wait for its report.

## Present it

Relay the findings grouped as the auditor returned them. Do not re-sort or
summarise into prose; the grouping is what lets the user fix one class at a
time.

Add one thing the auditor cannot: what this means for the next step. If the
epic is about to be handed to a worker loop, say plainly whether it is safe to
run. A cycle or a child failing the definition of ready means no. Edges onto
closed beads and a few stale entries usually mean yes, with those beads likely
to be picked up earlier than expected.

## Offer the fix path

Faults split into two piles and they get fixed differently.

Mechanical ones, meaning stale edges onto closed beads and missing parents,
have a single obvious correction each. Offer to fix them here, one at a time,
with the user confirming each.

Everything else, meaning rewrites, splits, decisions and duplicates, is a
grooming conversation. Say so and point at `/backlog-groom EPIC-ID`. Do not
start rewriting beads inside an audit; the user came for a report and a long
editing session is not what they asked for.

## Never

* Fix a fault the auditor reported without confirming that specific fix.
* Close or delete a bead.
* Run `bd cleanup` or `bd compact`.
* Declare an epic safe to run unattended when anything failed the definition of
  ready. A worker that claims an unready bead spends a whole session finding
  out, and the failure looks like a model problem rather than a backlog one.
