#!/usr/bin/env bash
set -u

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$WORKDIR/.venv/bin/python"
LOG_DIR="$HOME/logs"
LOG_FILE="$LOG_DIR/auto-absen-telegram.log"
LOCK_FILE="$HOME/.auto-absen-telegram.lock"

if [ ! -x "$PYTHON" ]; then
  echo "[FAIL] Project virtualenv not found at $PYTHON." >&2
  exit 1
fi
if ! command -v flock >/dev/null 2>&1; then
  echo "[FAIL] flock is required to prevent duplicate bot workers." >&2
  exit 1
fi

mkdir -p "$LOG_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  exit 0
fi

while true; do
  "$PYTHON" -u "$WORKDIR/run_telegram_bot.py" >> "$LOG_FILE" 2>&1
  sleep 30
done
