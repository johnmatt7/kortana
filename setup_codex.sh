#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/workspace/kortana"
PYTHON_BIN="python3"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN is not installed or not in PATH." >&2
  exit 1
fi

"$PYTHON_BIN" -m pip install --upgrade pip

if [ ! -d "$REPO_DIR" ]; then
  echo "Error: Repository directory '$REPO_DIR' does not exist." >&2
  exit 1
fi

cd "$REPO_DIR"

if [ ! -f "requirements.txt" ]; then
  echo "Error: requirements.txt not found in $REPO_DIR." >&2
  exit 1
fi

"$PYTHON_BIN" -m pip install -r requirements.txt

echo "Setup completed successfully."
