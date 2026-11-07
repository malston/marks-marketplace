---
description: Generate a recovery prompt to include context for the next session
---

# Recovery Prompt

The current context window is running low. Provide a recovery prompt to assist with the completion of this feature in a follow-up session.

## Rules

- Only include what still matters. Skip abandoned ideas unless they
  explain a decision.
- Be specific. File names, function names, numbers, exact wording.
- If you're unsure about something, flag it instead of guessing.

## Output location (required)

Always save the recovery prompt to `.prompts/<description>.prompt.md`, relative to the current working directory:

- Create the `.prompts/` directory in the current project if it does not already exist.
- `<description>` is a short kebab-case slug for the feature or work in progress (e.g. `spend-approval-remediation`). Keep it descriptive and filename-safe.
- Always use the `.prompt.md` suffix.
- Write the filled-in handoff (below) as the file's contents, and make it self-contained so a fresh session can resume with no prior context: include the repo path, current branch/PR, exact test and verify commands, next steps, and any gotchas.

After writing the file, report the saved path and copy it to my clipboard.

## Handoff Template

### Prompt

1. Goal: what we're trying to finish, in one or two sentences.
2. Decisions made, with the reason for each if it isn't obvious.
3. Context. Who it's for, what you already know or tried, and any files or links. Claude can't read your mind or your inbox.
4. What good looks like. Format, length, tone. Paste an example if you have one.
5. Constraints. What to avoid, and what must be true.
6. Preferences I've set (style rules, tools, versions, naming, things to avoid)
7. Current state: what's done, what's in progress, the latest version of any code or text we settled on (full text, not a description)
8. Open questions and known problems
9. Next step: the exact thing to do first in the new session

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
