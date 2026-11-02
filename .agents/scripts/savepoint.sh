#!/usr/bin/env bash
# Named save point of the whole working tree (tracked + untracked, not ignored) as a stash entry.
# Does NOT modify the working tree, the index or any branch: safe while other sessions work here.
# Usage:   savepoint.sh <role> <label>      e.g. savepoint.sh implementer "before step 4"
# List:    git stash list | grep 'savepoint:'
# Inspect: git diff HEAD <hash> --stat   (untracked files are in the main tree)
# Copy:    git archive <hash> | tar -x -C <dir>   (a scratch copy for reviews)
# Restore: NEVER on your own. Ask the coordinator; restoring overwrites other sessions' work.
set -euo pipefail
tag=${1:?role}; label=${2:?label}
root=$(git rev-parse --show-toplevel); cd "$root"
tmpidx=$(mktemp); trap 'rm -f "$tmpidx"' EXIT
cp "$(git rev-parse --git-path index)" "$tmpidx"
GIT_INDEX_FILE=$tmpidx git add -A
tree=$(GIT_INDEX_FILE=$tmpidx git write-tree)
msg="savepoint: [$tag] $label ($(date -u +%Y-%m-%dT%H:%MZ))"
idx=$(git commit-tree "$(git write-tree)" -p HEAD -m "index on savepoint")
c=$(git commit-tree "$tree" -p HEAD -p "$idx" -m "$msg")
git stash store -m "$msg" "$c"
echo "$msg -> $c"
mkdir -p "$root/.agents/tmp/coworking"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) [$tag] savepoint \`$c\`: $label" >> "$root/.agents/tmp/coworking/savepoints.md"
