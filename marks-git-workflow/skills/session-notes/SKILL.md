---
name: session-notes
description: Use at the end of a work session, before context compaction, or when switching tasks to capture structured observations for future sessions.
---

# Session Notes

Capture structured observations from the current session and save to claude-mem for cross-session search.

Replaces the need for separate observer agent sessions.

## When to Use

- End of any substantive work session
- Before context window compaction
- When switching to a different task
- When Mark asks to wrap up or save progress

## Instructions

### Step 1: Review the session

Scan the conversation for:

- **Goal**: What was attempted this session
- **Discoveries**: Technical findings, codebase insights, API behaviors
- **Decisions**: Design choices and their rationale
- **Files changed**: List with brief summaries
- **Gotchas**: Platform-specific issues, tooling quirks, failed approaches
- **Open items**: Unfinished work, known issues, follow-up tasks

### Step 2: Save observations

Save each significant observation as a separate claude-mem entry using `mcp__plugin_claude-mem_mcp-search__save_memory`. Use descriptive titles that are searchable.

Group by theme, not chronologically. Each entry should be self-contained -- a future session should understand it without reading the full conversation.

**Title format:** `<Project> - <Concise description>`

**Example entries:**

```
Title: "claudeup - ScopePrecedence uses map-based lookup for O(1) dedup"
Text: "Refactored ScopePrecedence from linear search to map-based lookup. The old approach relied on alphabetical ordering which broke when plugin names didn't sort in precedence order. Map-based approach uses explicit scope weights (user=0, project=1, local=2) for correct dedup regardless of naming."
```

```
Title: "claudeup - macOS /var symlink causes test path mismatches"
Text: "On macOS, /var is a symlink to /private/var. Tests comparing file paths must use filepath.EvalSymlinks() to normalize before comparison, or assertions fail with /var/... != /private/var/... even though they're the same path."
```

### Step 3: Flag memory-worthy items

If any discovery is stable enough for the project's MEMORY.md (confirmed across multiple sessions, not speculative), mention it to Mark and offer to add it.

Do NOT speculatively add to MEMORY.md -- only confirmed, durable patterns belong there.

## What NOT to save

- Session-specific context (temporary state, in-progress debugging)
- Information already in CLAUDE.md or MEMORY.md
- Speculative conclusions from reading a single file
- Exact code snippets (reference file paths instead)
