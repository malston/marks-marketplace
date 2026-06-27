# claude-plugin-marketplace

Private Claude Code marketplace of Mark's skills, packaged as thematic plugins.

## Install (per machine)

    claude plugin marketplace add malston/claude-plugin-marketplace
    claude plugin install marks-languages@claude-plugin-marketplace
    # ...repeat per plugin wanted on this machine

## Update

    git push                                   # publish changes
    claude plugin marketplace update claude-plugin-marketplace

To refresh an installed plugin after publishing:

    claude plugin uninstall <plugin>
    claude plugin install <plugin>@claude-plugin-marketplace

Note: `claude plugin update <plugin>` may report "Plugin not found" -- use uninstall/reinstall instead.

## Plugins

- **marks-languages** — language learning skills and review workflows
- **marks-dev-practice** — TDD, debugging, code review, and planning skills; commit/create-release/make-local-issue/recovery-prompt/update-memory commands; test-runner agent; pre-commit hooks
- **marks-git-workflow** — git and PR review workflow; commit-push-pr command; investigation-scratchpad skill; scratchpad enforcement hook
- **marks-vault** — Obsidian vault management skills and commands
- **marks-writing** — writing clarity, elements of style, and prose skills
- **marks-guardrails** — safety guardrails: block-dangerous-commands hook, protect-sensitive-files hook, markdown formatter hook
- **marks-iterm** — iTerm2 session save/restore; save-iterm-session hook (macOS + iTerm2 Python API required)
- **marks-vsphere** — vSphere infrastructure automation; vsphere-architect skill and command
