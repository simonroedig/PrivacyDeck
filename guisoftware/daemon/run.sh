#!/usr/bin/env bash
# PrivacyDeck daemon launcher
# Run from anywhere: bash daemon/run.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV="$SCRIPT_DIR/.venv"

# Create venv and install deps if needed
if [ ! -f "$VENV/bin/python" ]; then
  echo "[setup] Creating virtual environment..."
  python3 -m venv "$VENV"
fi

if ! "$VENV/bin/python" -c "import websockets" 2>/dev/null; then
  echo "[setup] Installing dependencies..."
  "$VENV/bin/pip" install -r requirements.txt
fi

echo "[daemon] Starting PrivacyDeck daemon..."
exec "$VENV/bin/python" main.py
