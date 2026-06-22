#!/usr/bin/env bash
# Set up the knowledge-mcp server on this machine: check prerequisites, build the venv.
# Run once per machine after cloning. Safe to re-run.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[setup] checking prerequisites..."
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found on PATH. Install git."; exit 1; }
PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "ERROR: python3 not found on PATH."; exit 1; }
"$PY" - <<'PYV' || { echo "ERROR: need Python >= 3.10"; exit 1; }
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PYV
echo "[setup] git: $(git --version)  |  python: $("$PY" --version 2>&1)"

echo "[setup] building venv at $DIR/.venv ..."
"$PY" -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install --quiet --upgrade pip
"$DIR/.venv/bin/pip" install --quiet -r "$DIR/requirements.txt"
"$DIR/.venv/bin/python" -c "import mcp; print('[setup] mcp import OK')"

REPO="$DIR/../knowledge"
if [ -d "$REPO/.git" ]; then
  echo "[setup] knowledge repo found: $REPO"
else
  echo "[setup] WARNING: knowledge repo not found at $REPO"
fi

echo "[setup] writing the MCP configs for this install path ..."
gen_cfg () {  # $1 = filename, rest = server args
  local f="$DIR/$1"; shift
  printf '{\n  "mcpServers": {\n    "knowledge": {\n      "command": "/bin/sh",\n      "args": ["-c", "exec \\"%s/start.sh\\" %s"]\n    }\n  }\n}\n' "$DIR" "$*" > "$f"
}
gen_cfg mcp.read.json    --mode read --version v1
gen_cfg mcp.read.v2.json --mode read --version v2
gen_cfg mcp.read.v3.json --mode read --version v3
gen_cfg mcp.manage.json  --mode manage
echo "[setup] configs now point at $DIR/start.sh (works in any folder)"

echo "[setup] done."
echo "[setup] verify with:  $DIR/.venv/bin/python $DIR/smoke_test.py"
