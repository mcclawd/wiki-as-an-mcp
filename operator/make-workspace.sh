#!/usr/bin/env bash
# make-workspace.sh — materialize a clean-room agent workspace for one condition.
#
# Usage:  operator/make-workspace.sh <condition> [dest]
#         <condition> = a folder name under conditions/   (wiki-0531 | wiki-0530 | no-wiki | exp-*)
#         [dest]      = workspace dir (default: ~/bench/ws-<condition>)
#
# The workspace contains ONLY what a benchmark agent may see:
#   - the agent contracts for that condition (CLAUDE/AGENTS/GEMINI.md)
#   - knowledge-base/ (if the condition has one)
#   - the task spec (plan_v5.md, checklist_v5.md)
#   - CONDITION.txt (provenance stamp: condition, repo SHA, wiki version, time)
# It deliberately does NOT contain: conditions/, do_not_read/, paper/, FINDINGS.md,
# OPERATOR.md, README.md, MASTER.md, RUNBOOK.md, evaluator/, operator/ — the agent
# cannot read what is not there.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COND="${1:?usage: make-workspace.sh <condition> [dest]}"
SRC="$REPO/conditions/$COND"
DEST="${2:-$HOME/bench/ws-$COND}"

[ -d "$SRC" ] || { echo "ERROR: no such condition: $SRC"; ls "$REPO/conditions/"; exit 1; }

if [ -d "$DEST" ]; then
  echo "Workspace exists: $DEST — refreshing condition payload + spec (runs untouched)."
else
  mkdir -p "$DEST"
fi

# 1) condition payload: contracts (+ knowledge-base if present)
cp "$SRC"/CLAUDE.md "$SRC"/AGENTS.md "$SRC"/GEMINI.md "$DEST/" 2>/dev/null || \
  { echo "ERROR: condition payload missing contracts"; exit 1; }
rm -rf "$DEST/knowledge-base"
if [ -d "$SRC/knowledge-base" ]; then
  cp -R "$SRC/knowledge-base" "$DEST/knowledge-base"
fi

# 2) task spec (invariant core)
cp "$REPO/plan_v5.md" "$REPO/checklist_v5.md" "$DEST/"

# 3) provenance stamp — recorded fact, not a label
REPO_SHA="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo 'no-git')"
WIKI_LINE="$(head -1 "$SRC/knowledge-base/WIKI_VERSION.txt" 2>/dev/null || head -1 "$SRC/WIKI_VERSION.txt" 2>/dev/null || echo 'wiki snapshot: 0 (no knowledge base)')"
cat > "$DEST/CONDITION.txt" <<EOF
condition: $COND
repo_sha: $REPO_SHA
$WIKI_LINE
materialized: $(date -u +%Y-%m-%dT%H:%M:%SZ)
by: make-workspace.sh
EOF

echo "OK: $COND -> $DEST"
echo "   $(grep -c . "$DEST/CONDITION.txt") stamp lines; knowledge-base: $([ -d "$DEST/knowledge-base" ] && echo present || echo ABSENT)"
echo "Verify with: operator/check-structure.sh \"$DEST\""
