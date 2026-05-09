#!/usr/bin/env bash
# glancely — one-shot installer for ClawHub skill.
#
#     pip install glancely
#     glancely setup
#
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

step() { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }

if ! "$PYTHON_BIN" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"; then
  echo "Need Python 3.9+; have $($PYTHON_BIN --version)"; exit 1
fi

step "Installing glancely package"
"$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
"$PYTHON_BIN" -m pip install -e "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

step "Running setup (migrations only)"
glancely setup

cat <<EOF

Done. Try it:
  glancely list
  glancely version

To create your first tracker:
  Just tell your agent what you want to track!
EOF
