#!/usr/bin/env bash
# check-structure.sh — verify a materialized workspace matches its CONDITION.txt stamp.
# Run BEFORE every launch. Deterministic, no LLM.
#
# Usage:  operator/check-structure.sh <workspace-dir>
#
# Checks:
#   1. CONDITION.txt exists and names a condition that exists in the repo
#   2. workspace contracts == conditions/<name>/ contracts (byte-identical)
#   3. workspace knowledge-base == conditions/<name>/knowledge-base (or both absent)
#   4. task spec == repo core spec
#   5. nothing radioactive leaked in (conditions/, do_not_read/, paper/, FINDINGS.md)
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="${1:?usage: check-structure.sh <workspace-dir>}"
FAIL=0
note() { echo "  $1"; }
fail() { echo "  FAIL: $1"; FAIL=1; }

[ -f "$WS/CONDITION.txt" ] || { echo "FAIL: no CONDITION.txt in $WS"; exit 1; }
COND="$(awk -F': ' '/^condition:/{print $2}' "$WS/CONDITION.txt")"
SRC="$REPO/conditions/$COND"
echo "== check-structure: $WS  (stamped condition: $COND) =="
[ -d "$SRC" ] || { echo "FAIL: stamped condition '$COND' not found in repo"; exit 1; }

# 2) contracts
for f in CLAUDE.md AGENTS.md GEMINI.md; do
  if ! diff -q "$WS/$f" "$SRC/$f" >/dev/null 2>&1; then fail "contract drift: $f"; else note "contract ok: $f"; fi
done

# 3) knowledge-base
if [ -d "$SRC/knowledge-base" ]; then
  if [ ! -d "$WS/knowledge-base" ]; then fail "knowledge-base missing (condition has one)"
  elif d=$(diff -rq "$WS/knowledge-base" "$SRC/knowledge-base" 2>&1 | grep -v '.DS_Store'); [ -n "$d" ]; then
    fail "knowledge-base drift:"; echo "$d" | head -5
  else note "knowledge-base ok ($(find "$WS/knowledge-base" -type f | wc -l | tr -d ' ') files)"; fi
else
  if [ -d "$WS/knowledge-base" ]; then fail "knowledge-base PRESENT but condition is no-wiki"; else note "no knowledge-base (correct for $COND)"; fi
fi

# 4) spec
for f in plan_v5.md checklist_v5.md; do
  if ! diff -q "$WS/$f" "$REPO/$f" >/dev/null 2>&1; then fail "spec drift: $f"; else note "spec ok: $f"; fi
done

# 5) radioactive material must be absent
for p in conditions do_not_read paper FINDINGS.md OPERATOR.md MASTER.md RUNBOOK.md; do
  [ -e "$WS/$p" ] && fail "leak: $p exists in workspace"
done
[ $FAIL -eq 0 ] && note "no operator/analysis material present"

if [ $FAIL -eq 0 ]; then echo "PASS — workspace matches its stamp"; else echo "FAILED — do not launch from this workspace"; fi
exit $FAIL
