#!/usr/bin/env bash
# setup-repo.sh KIND
#
# Builds the sample sbxcli repository a beads-pm eval case runs against, in the
# current directory (the eval run's empty workspace). Called from each case's
# scaffold.sh, which claude plugin eval runs only under --scaffold.
#
#   backlog  .beads/ holding epic sbx-56e and its seven children, with planted
#            faults (stale edge, decision filed as work, duplicate, oversized
#            bead, bead with no files or test). Used by backlog-audit and
#            backlog-groom cases.
#   plan     an empty .beads/ plus plan.md. Used by plan-to-beads cases.
#
# Both kinds get .claude/definition-of-ready.md with the project specifics
# filled in, since every skill refuses to work without it.
set -Eeuo pipefail

readonly HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kind="${1:?usage: setup-repo.sh backlog|plan}"

git init -q
git config user.name "beads-pm eval"
git config user.email "eval@example.invalid"

mkdir -p .claude src/sbxcli tests
cp "$HERE/definition-of-ready.md" .claude/definition-of-ready.md
: > src/sbxcli/__init__.py

bd init --prefix sbx --non-interactive --skip-agents --skip-hooks -q
bd metrics off >/dev/null

case "$kind" in
    backlog) bd import "$HERE/sbx-backlog.jsonl" >/dev/null ;;
    plan)    cp "$HERE/plan.md" plan.md ;;
    *)       echo "setup-repo.sh: unknown kind: $kind" >&2; exit 1 ;;
esac
