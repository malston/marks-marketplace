---
name: pr-review-fix
description: Use when a PR has review comments that need to be addressed, when asked to fix PR review items, or after receiving code review feedback that requires code changes.
argument-hint: <PR-number or URL>
---

# PR Review Fix

Fetch, evaluate, fix, test, commit, and resolve all review comments on a pull request.

**REQUIRED:** Use `superpowers:receiving-code-review` to evaluate each comment. Verify before implementing. Push back on wrong suggestions.

## Instructions

### Step 1: Fetch review comments

Parse the argument (PR number or URL). If none provided, ask.

```bash
# PR metadata and review status
gh pr view <PR> --json number,title,state,author,reviewDecision,headRefName

# Inline review comments (need IDs for replies later)
gh api repos/{owner}/{repo}/pulls/<PR>/comments \
  --jq '.[] | {id: .id, path: .path, line: .line, body: .body, user: .user.login, in_reply_to_id: .in_reply_to_id}'

# General PR conversation
gh pr view <PR> --comments

# Changed files for context
gh pr diff <PR> --name-only
```

### Step 2: Self-review the diff

Before addressing reviewer comments, scan the PR diff for issues reviewers may have missed:

```bash
gh pr diff <PR>
```

Check against this checklist:

- [ ] All new code paths have unit tests
- [ ] No non-deterministic ordering (unsorted map iteration, slice output)
- [ ] Edge cases handled (empty inputs, nil values, duplicate entries)
- [ ] Security-sensitive changes have explicit edge case tests
- [ ] No test assertions weakened to make tests pass
- [ ] No accidental debug code, TODOs, or commented-out blocks

Flag any self-review findings alongside the reviewer comments in Step 3.

### Step 3: Categorize and confirm scope

Categorize each comment (including self-review findings):

- **Blocking**: Must fix (bugs, security, logic errors, explicit requests)
- **Suggestions**: Worth considering (style, alternatives)
- **Questions**: Need answers
- **Already resolved**: Skip

Present categorized items with your technical assessment of each. Ask Mark which to address -- don't assume all suggestions should be implemented.

### Step 4: Fix items

Work through confirmed items in priority order (blocking > simple > complex). For each:

1. Read the relevant file
2. Implement the fix
3. If the fix touches security-related code, add edge case tests proactively

### Step 5: Run tests

Run the project's full test suite. All tests must pass. If a test fails, fix the root cause -- never weaken assertions to make tests pass.

### Step 6: Commit and push

```bash
# Verify correct branch
git branch --show-current

# Stage specific files, commit, push
git add <files>
git commit -m "fix: address PR review feedback

- <item 1 summary>
- <item 2 summary>"

git push
```

### Step 7: Reply to comment threads

Reply in each original comment thread with a brief technical note:

```bash
gh api repos/{owner}/{repo}/pulls/<PR>/comments/<comment-id>/replies \
  -f body="Fixed. <what changed>"
```

No performative gratitude. State the fix and move on.

### Step 8: Report

Summarize for Mark:

- Items fixed (with file locations)
- Items skipped (with reason)
- Items needing Mark's input
- Test results
- Commit hash

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- Write access to the repository
- Locally checked out on the PR's branch
