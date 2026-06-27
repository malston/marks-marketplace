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
