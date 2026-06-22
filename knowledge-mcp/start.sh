#!/usr/bin/env bash
# Self-locating launcher (rule 7): works wherever this folder is cloned.
# Runs the doctor health check on EVERY start (set KMCP_SKIP_DOCTOR=1 to skip), then execs
# the server. Doctor output goes to stderr so it never touches the MCP stdio channel.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${KMCP_SKIP_DOCTOR:-0}" != "1" ]; then
  if ! "$DIR/doctor.sh" 1>&2; then
    echo "[knowledge-mcp] doctor found a problem; not starting. Fix the above (usually: run $DIR/setup.sh)." >&2
    exit 1
  fi
fi

exec "$DIR/.venv/bin/python" "$DIR/server.py" "$@"
