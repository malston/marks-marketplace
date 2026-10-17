---
description: Generate a recovery prompt to include context for the next session
---

# Recovery Prompt

The current context window is running low. Provide a recovery prompt to assist with the completion of this feature in a follow-up session.

## Output location (required)

Always save the recovery prompt to `.prompts/<description>.prompt.md`, relative to the current working directory:

- Create the `.prompts/` directory in the current project if it does not already exist.
- `<description>` is a short kebab-case slug for the feature or work in progress (e.g. `spend-approval-remediation`). Keep it descriptive and filename-safe.
- Always use the `.prompt.md` suffix.
- Write the filled-in handoff (below) as the file's contents, and make it self-contained so a fresh session can resume with no prior context: include the repo path, current branch/PR, exact test and verify commands, next steps, and any gotchas.

After writing the file, report the saved path.

## Handoff Template

### Progress Summary

[Completed tasks]

### Current State

[What's working, what's blocked]

### Next Steps

1. [Immediate priority]
2. [Secondary task]
3. [Future consideration]

### Gotchas

- [Rules, traps or wrong turns the next session must know about]

### Questions for Team

- [Specific question 1]
- [Specific question 2]
