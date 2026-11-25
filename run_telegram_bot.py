"""Run the Telegram command worker using long polling on a VPS."""

import time

from app.config import settings

from app.telegram_commands import handle_update
from app.utils.telegram import get_updates, get_webhook_info, send_message

RETRY_DELAY_SECONDS = 5


def main() -> int:
    if not all(
        (
            settings.telegram_bot_token.strip(),
            settings.telegram_chat_id.strip(),
        )
    ):
        print("[FAIL] Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return 1

    webhook_info = get_webhook_info()
    if webhook_info is None:
        print("[FAIL] Could not verify the Telegram bot token with Telegram.")
        return 1
    if webhook_info.get("url"):
        print("[FAIL] This bot has a webhook configured; remove it before using long polling.")
        return 1

    print("[OK] Telegram logbook worker started.")
    offset = None
    while True:
        updates = get_updates(offset)
        if updates is None:
            print("[WARN] Telegram polling failed; retrying shortly.")
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        for update in updates:
            update_id = update.get("update_id")
            try:
                result = handle_update(update, settings.telegram_chat_id)
                if result:
                    chat_id, reply = result
                    if not send_message(chat_id, reply):
                        print("[WARN] Telegram reply failed to send.")
            except Exception:
                print("[WARN] Telegram update processing failed.")

            if isinstance(update_id, int):
                offset = max(offset or 0, update_id + 1)


if __name__ == "__main__":
    raise SystemExit(main())
