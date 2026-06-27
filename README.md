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

- marks-languages, marks-dev-practice, marks-git-workflow, marks-vault, marks-writing
