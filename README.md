# marks-marketplace

Private Claude Code marketplace of Mark's skills, packaged as thematic plugins.

## Install (per machine)

    claude plugin marketplace add malston/marks-marketplace
    claude plugin install marks-languages@marks-marketplace
    # ...repeat per plugin wanted on this machine

## Update

    git push                                   # publish changes
    claude plugin marketplace update marks-marketplace

To refresh an installed plugin after publishing:

    claude plugin uninstall <plugin>
    claude plugin install <plugin>@marks-marketplace

Note: `claude plugin update <plugin>` may report "Plugin not found" -- use uninstall/reinstall instead.

## Plugins

- **marks-languages** — per-language coding standards: bash, go, python, rust, typescript
- **marks-dev-practice** — clean-architecture, TDD, tdd-pr, epic-loop, scoping-context-for-subagents, explain-code skills; test-runner agent; dev-workflow + promptengineering commands
- **marks-git-workflow** — commit-helper, pr-comments, pr-review-fix, session-notes, investigation-scratchpad skills; commit/create-release/make-local-issue/recovery-prompt/update-memory commands; scratchpad-nudge hook
- **marks-vault** — Obsidian vault tooling: date-slug-rename, vlt-skill, dream
- **marks-writing** — the-antislop (detect/fix AI-generated prose)
- **marks-guardrails** — safety/format hooks: block-dangerous-commands, protect-sensitive-files, format-on-save, log-bash-commands, markdown_formatter
- **marks-iterm** — iTerm2 session-save command + bin script (macOS + iTerm2 Python API required)
- **marks-vsphere** — vsphere-architect skill + vSphere design commands
- **marks-book-knowledge** — knowledge bases distilled from books: core-kubernetes, terraform-in-depth, software-security-for-developers, system-design-interview
- **marks-forgd-training** — Forgd session tooling: ask/deep/eli5 references, deck-coach, teleprompter-script
- **marks-cca** — CCA-Foundations exam prep: format-practice, practice-coach, quiz
- **marks-ai-eng** — AI engineering helpers: llm-api-builder, prompt-lookup, claude-docs-consultant
- **engineer-grade-agent-skills** — 90 production engineering skills (clean code, TDD, DDD, architecture, messaging, languages, observability, agents) + 6 commands + a documented pre-commit quality-gate pattern (reference only, not a wired hook); vendored from roanbrasil/engineer-grade-agent-skills (MIT)
