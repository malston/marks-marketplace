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

# epoch_to_iso SECONDS: GNU date takes -d @N, BSD date takes -r N.
epoch_to_iso() {
    date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -r "$1" +%Y-%m-%dT%H:%M:%SZ
}

# stamp_ages FILE: print the JSONL with created_at/updated_at set one hour
# apart in file order, ending an hour ago. Filing order is what "oldest first"
# means to backlog-groom, so it has to be defined; dating it relative to now
# keeps the fixture from drifting into "stale" as it ages.
stamp_ages() {
    local now n i=0 ts line
    now="$(date -u +%s)"
    n="$(wc -l < "$1")"
    while IFS= read -r line; do
        ts="$(epoch_to_iso $((now - 3600 * (n - i))))"
        printf '{"created_at":"%s","updated_at":"%s",%s\n' "$ts" "$ts" "${line#\{}"
        i=$((i + 1))
    done < "$1"
}

git init -q
git config user.name "beads-pm eval"
git config user.email "eval@example.invalid"

mkdir -p .claude src/sbxcli tests
cp "$HERE/definition-of-ready.md" .claude/definition-of-ready.md
: > src/sbxcli/__init__.py

bd init --prefix sbx --non-interactive --skip-agents --skip-hooks -q
bd metrics off >/dev/null

case "$kind" in
    backlog) stamp_ages "$HERE/sbx-backlog.jsonl" | bd import - >/dev/null ;;
    plan)    cp "$HERE/plan.md" plan.md ;;
    *)       echo "setup-repo.sh: unknown kind: $kind" >&2; exit 1 ;;
esac
