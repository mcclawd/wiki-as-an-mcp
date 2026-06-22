#!/usr/bin/env bash
# doctor: health checks for the knowledge-mcp server.
# Runs automatically from start.sh on EVERY start, and is runnable on its own to diagnose.
# Exit 0 = healthy; non-zero = a problem (each line says the fix). Self-locating (rule 7).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/.venv/bin/python"
REPO="$DIR/../knowledge"
fail=0
ok()  { printf '  %-16s OK   %s\n' "$1" "$2"; }
bad() { printf '  %-16s BAD  %s\n' "$1" "$2"; fail=1; }

echo "[doctor] knowledge-mcp health check"

# 1) git on PATH (the wiki is a git repo)
if command -v git >/dev/null 2>&1; then ok "git" "$(git --version | awk '{print $3}')"
else bad "git" "not on PATH; install git"; fi

# 2) venv exists and the mcp package imports
if [ -x "$PY" ] && "$PY" -c "import mcp" >/dev/null 2>&1; then ok "venv + mcp" "$("$PY" --version 2>&1)"
else bad "venv + mcp" "missing/broken; run $DIR/setup.sh (a venv cannot be moved)"; fi

# 3) knowledge repo present with its arms
if [ -d "$REPO/.git" ]; then
  arms="$(git -C "$REPO" for-each-ref --format='%(refname:short)' refs/heads 2>/dev/null | tr '\n' ' ')"
  if printf ' %s ' "$arms" | grep -q ' v1 '; then ok "knowledge repo" "arms: ${arms% }"
  else bad "knowledge repo" "no v1 branch (arms: ${arms:-none})"; fi
else bad "knowledge repo" "not found at $REPO"; fi

# 4) MCP config files are valid JSON
if [ -x "$PY" ]; then
  cfg_bad=0
  for c in "$DIR"/mcp.*.json; do
    [ -e "$c" ] || continue
    "$PY" -c "import json,sys; json.load(open(sys.argv[1]))" "$c" >/dev/null 2>&1 \
      || { bad "config" "invalid JSON: $(basename "$c")"; cfg_bad=1; }
  done
  [ "$cfg_bad" = 0 ] && ok "configs" "valid JSON"
fi

if [ "$fail" = 0 ]; then echo "[doctor] healthy"; else echo "[doctor] PROBLEMS FOUND (see above)"; fi
exit "$fail"
