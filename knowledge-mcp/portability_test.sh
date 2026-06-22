#!/usr/bin/env bash
# Portability test: copy the whole project to a temporary path and run the smoke test
# there. The server, the test, and the wiki repo all locate themselves relative to their
# own position, so the copy must pass from a different path. If any machine-specific
# absolute path has leaked back in, the copy fails here. Reuses the existing venv's
# interpreter (no reinstall), but runs the COPY's code and its own copy of the git repo.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # knowledge-mcp/
ROOT="$(cd "$DIR/.." && pwd)"                            # knowledge-mcp-design/
PY="$DIR/.venv/bin/python"
[ -x "$PY" ] || { echo "no venv; run setup.sh first"; exit 1; }

BASE="$(mktemp -d)"; TMP="$BASE/kmcp-copy"
echo "[port-test] copying project to $TMP ..."
mkdir -p "$TMP"
cp -r "$ROOT/." "$TMP/"
rm -rf "$TMP/knowledge-mcp/.venv" "$TMP/knowledge-mcp/__pycache__" "$TMP/knowledge-mcp/logs"

echo "[port-test] running the smoke test from the COPY at a new path ..."
if "$PY" "$TMP/knowledge-mcp/smoke_test.py" 2>&1 | grep -q "ALL CHECKS PASSED"; then
  echo "[port-test] PASS: works from a different path, no absolute-path regressions"
  rc=0
else
  echo "[port-test] FAIL: the copy did not pass; an absolute path likely leaked in"
  rc=1
fi
rm -rf "$BASE"
exit $rc
