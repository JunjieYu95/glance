#!/usr/bin/env bash
# glance — one-shot installer.
#
# This script is a thin wrapper around `pip install glance` for
# users who clone the repo directly. The supported install path is `pip`:
#
#     pip install glance
#     glance setup
#
# Run this script from a clone of the repo to do the same thing locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

step() { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m!!  %s\033[0m\n" "$*"; }

if ! "$PYTHON_BIN" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)"; then
  echo "Need Python 3.9+; have $($PYTHON_BIN --version)"; exit 1
fi

step "1/2  Installing the glance package (editable)"
"$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
"$PYTHON_BIN" -m pip install -e "$REPO_ROOT"

step "2/2  Running first-time setup"
if ! command -v glance >/dev/null 2>&1; then
  warn "The 'glance' command isn't on PATH. Add your user pip-bin dir to PATH and retry:"
  warn "    export PATH=\"\$($PYTHON_BIN -c 'import site,os;print(os.path.join(site.getuserbase(),\"bin\"))'):\$PATH\""
  exit 1
fi
glance setup

cat <<EOF

Done. Try it:
  glance help
  glance list
  glance dashboard open

To track something new (e.g. coffee):
  glance scaffold --name coffee_intake --title "Coffee" \\
      --field shots:int --cron "0 9 * * *" --notify "How much coffee today?"
EOF
