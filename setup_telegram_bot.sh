#!/usr/bin/env bash
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$WORKDIR/run_telegram_bot.sh"
MARKER="# TelegramLogbookWorker"

if ! command -v crontab >/dev/null 2>&1; then
  echo "[FAIL] crontab is not installed." >&2
  exit 1
fi
if [ ! -x "$RUNNER" ]; then
  echo "[FAIL] Bot runner is not executable: $RUNNER" >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
(crontab -l 2>/dev/null || true) | grep -F -v "$MARKER" > "$TMP" || true
printf '@reboot "%s" %s\n' "$RUNNER" "$MARKER" >> "$TMP"
crontab "$TMP"

nohup "$RUNNER" >/dev/null 2>&1 </dev/null &
echo "[OK] Telegram worker is scheduled at reboot and starting now."
echo "Log: $HOME/logs/auto-absen-telegram.log"
echo "Check: pgrep -af run_telegram_bot.py"
