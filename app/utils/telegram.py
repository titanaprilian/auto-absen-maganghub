"""Telegram Bot API helpers for notifications and long polling."""

import json

import requests

from app.api.client import TIMEOUT
from app.config import settings

MESSAGE_LIMIT = 3900
LONG_POLL_SECONDS = 25


def _get_result(method: str, params: dict | None = None, timeout: int = TIMEOUT):
    token = settings.telegram_bot_token.strip()
    if not token:
        return None

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/{method}",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None
    return payload.get("result")


def get_webhook_info() -> dict | None:
    """Return webhook metadata without exposing the bot token or URL."""
    result = _get_result("getWebhookInfo")
    return result if isinstance(result, dict) else None


def get_updates(offset: int | None) -> list[dict] | None:
    """Long-poll for message updates, returning None when the API request fails."""
    params = {
        "timeout": LONG_POLL_SECONDS,
        "allowed_updates": json.dumps(["message"]),
    }
    if offset is not None:
        params["offset"] = offset
    result = _get_result("getUpdates", params, timeout=LONG_POLL_SECONDS + 10)
    if not isinstance(result, list):
        return None
    return [update for update in result if isinstance(update, dict)]


def send_message(chat_id: str, text: str) -> bool:
    """Send plain-text messages, split into Telegram-safe chunks if needed."""
    token = settings.telegram_bot_token.strip()
    if not token:
        return False

    for start in range(0, len(text), MESSAGE_LIMIT):
        chunk = text[start : start + MESSAGE_LIMIT]
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return False
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            return False
    return True
