---
name: isolate-claude-config-profile
description: "Use when a Claude Code session started with CLAUDE_CONFIG_DIR still loads instructions, rules, plugins or skills from the default ~/.claude setup. Explains how to find and close each leak."
metadata:
  origin: auto-extracted
---

# Isolating a Claude Code config profile

**Extracted:** 2026-09-29
**Context:** Running a second Claude Code profile with `CLAUDE_CONFIG_DIR=~/.claude-<name> claude` and wanting nothing from the normal profile in it.

## Problem

`CLAUDE_CONFIG_DIR` moves only user-level paths. Other routes still reach the session:

1. **Parent-directory loading.** Claude Code loads `CLAUDE.md` and `.claude/rules/*.md` from every parent of the start directory. Starting anywhere under `~` reaches `~/.claude/`, so `~/.claude/CLAUDE.md` and `~/.claude/rules/*.md` load as project files.
2. **AGENTS.md fallback.** When no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above, Claude Code reads `AGENTS.md` from there, including `~/AGENTS.md`. The session shows `no CLAUDE.md found; AGENTS.md loaded: <path>`.
3. **claude.ai sync.** Plugins and skills enabled on the claude.ai account sync into every profile.
4. **Plugin data paths.** A plugin may hard-code `~/.claude` or read its own env var instead of `CLAUDE_CONFIG_DIR`. For example, ECC uses `ECC_AGENT_DATA_HOME`.
5. **Config tools run from the profile's shell.** A session started with `CLAUDE_CONFIG_DIR` passes it to every command it runs. Tools that honor it then write into the profile. `claudeup ext enable skills <one>` run from such a session linked all 82 enabled claudeup skills into `<profile>/skills`, not just the one named.

## Solution

In `<profile>/settings.json`:

```json
{
  "claudeMdExcludes": [
    "/Users/<you>/.claude/CLAUDE.md",
    "/Users/<you>/.claude/rules/**",
    "/Users/<you>/AGENTS.md"
  ],
  "syncClaudeAiPlugins": false,
  "syncClaudeAiSkills": false
}
```

- If the files in `~/.claude/rules/` are symlinks, also exclude the directory they point to.
- `claudeMdExcludes` applies to `AGENTS.md` files too.
- Run tools meant for the normal profile with the variable unset, for example `env -u CLAUDE_CONFIG_DIR claudeup ...`. Afterwards, check that the profile's `skills/`, `rules/`, `agents/` and `commands/` gained nothing.
- For plugins, grep the plugin's scripts for `homedir()` and `.claude` to find where it writes. Set its override env var in the profile's `env`, and report hard-coded paths upstream.

## Verify

Start a fresh session in a directory with no `CLAUDE.md` on the path, because the `AGENTS.md` leak only shows up there. Run `/memory`: it should list only the profile's files and the project's own.

- `/memory`'s "User instructions" row can say "Saved in ~/.claude/CLAUDE.md" but open `<profile>/CLAUDE.md`. The label is only wording.
- Choosing "Project instructions" creates an empty `./CLAUDE.md`, which then stops `AGENTS.md` from loading in that repo. Delete it after checking.

## When to Use

- Setting up a second profile with `CLAUDE_CONFIG_DIR`.
- `/memory` in such a profile lists files from `~/.claude` or `~/AGENTS.md`.
- Skills or plugins you never installed in the profile show up in it.
