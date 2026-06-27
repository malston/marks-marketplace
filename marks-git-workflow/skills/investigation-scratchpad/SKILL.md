---
name: investigation-scratchpad
description: >-
  Bootstrap and maintain a SCRATCHPAD.md trail for a multi-step code
  investigation -- the running record of hypotheses, findings, and explicitly
  ruled-out dead ends. Invoke this explicitly when you want that structured,
  persistent trail for a debugging or audit session. Note on triggering: for
  general bug/debugging entry, systematic-debugging is the skill that fires; the
  durable enforcement of trail updates is the scratchpad-nudge hook (see below).
  This skill supplies the template and discipline on request.
user-invocable: true
---

# Investigation Scratchpad

When an investigation will take more than a couple of steps, the trail of what
you tried -- and what you ruled out -- is worth more than any single finding. A
running `SCRATCHPAD.md` gives you durable working memory: you stop re-checking
things you already checked, you can pick the thread back up after a compaction,
and the dead-ends you mark today save the _next_ investigation that wanders into
the same territory.

This skill is the bootstrap-and-maintain layer, invoked on request. It does not
try to auto-trigger on debugging prompts -- `systematic-debugging` already owns
that entry point and wins that contest. The durable mechanism here is the
`scratchpad-nudge` hook (see the end): it fires on every tool call regardless of
which skill is active, so the trail gets kept even when no skill is in play. Use
this skill when you want the template and structure laid down explicitly.

## When to start a pad

Start one as soon as you realize the task is exploratory: a bug with an unknown
cause, a "why does X happen" question, a regression hunt, a cross-file audit, or
any research that'll take several steps. If it's a one-step lookup, skip it --
the value is the trail, and a single entry isn't a trail.

## Bootstrap

Before your next investigative tool call, create `SCRATCHPAD.md` at the repo root
(or the working directory if there's no repo) with this template:

```markdown
# Investigation: <short title>

**Status**: in-progress

## Goal

<restate the question in your own words -- this catches misunderstandings early>

## Hypotheses

- [ ] H1: ...
- [ ] H2: ...

## Trail

<append step-by-step findings here>

## Dead Ends

<things ruled out -- don't revisit>

## Summary

<fill in at the end>
```

Restating the goal in your own words is not busywork -- it's the cheapest moment
to catch a misread of what's actually being asked.

## Maintain the trail

After each meaningful investigative step (a search, a file read that taught you
something, a hypothesis you tested), append a terse entry to `## Trail`:

- **Step N** -- what you did
- **Finding** -- what you learned, or that it was inconclusive
- **Next** -- what you'll try next, or "done"

Keep entries to bullet points, not paragraphs. Update the hypothesis checkboxes
as you confirm or refute them.

When you rule something out, record it under `## Dead Ends` with a one-line
reason. This is the highest-leverage habit: an explicit dead-end is what stops
you (and future investigations) from circling back to a path that doesn't lead
anywhere.

## Close it out

Before you report your conclusion, write `## Summary` at the top and set
`**Status**` to `complete`. The summary should let someone read just that section
and understand what you found and why.

## Practical notes

- **Treat it as ephemeral.** The pad is working memory, not a deliverable. Add
  `SCRATCHPAD.md*` to `.gitignore` so investigation noise never lands in a PR.
- **One pad per investigation.** For parallel threads, give each a slug:
  `SCRATCHPAD-goroutine-leak.md`, `SCRATCHPAD-auth-500s.md`.
- **The trail is the artifact.** Even after the bug is fixed, the dead-ends and
  the reasoning are what pay off next time. Don't delete it mid-session to "clean
  up."

## Enforcement companion (optional)

A skill is advisory -- on long sessions it's easy to stop touching the pad. If
that drift is a problem, add a `PostToolUse` hook that nudges when
`SCRATCHPAD.md` exists but has gone stale. The hook is what actually enforces the
habit; this skill just gets the structure in place from step one.

`.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash|Grep|Read|Glob",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/scratchpad-nudge.sh" }
        ]
      }
    ]
  }
}
```

`.claude/hooks/scratchpad-nudge.sh` (make it executable):

```bash
#!/usr/bin/env bash
set -euo pipefail

PAD="SCRATCHPAD.md"
[[ -f "$PAD" ]] || exit 0  # no pad, no investigation in progress

last_mod=$(stat -c %Y "$PAD" 2>/dev/null || stat -f %m "$PAD")
now=$(date +%s)
if (( now - last_mod > 90 )); then
  echo "[scratchpad-nudge] SCRATCHPAD.md is stale. Append a Trail entry for the step you just completed before continuing." >&2
  exit 2  # exit code 2 surfaces stderr back to Claude as a system reminder
fi
```

Exit code 2 feeds the message back into context as a reminder rather than
blocking the tool call -- the right primitive for "you forgot something."
