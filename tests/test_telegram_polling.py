import app.telegram_commands as telegram_commands
import app.utils.telegram as telegram_transport


def test_update_handler_accepts_only_the_configured_private_chat(monkeypatch):
    monkeypatch.setattr(
        telegram_commands,
        "handle_command",
        lambda text: "Logbook reply" if text == "/logbook" else None,
    )

    result = telegram_commands.handle_update(
        {
            "message": {
                "chat": {"id": 12345, "type": "private"},
                "text": "/logbook",
            }
        },
        "12345",
    )
    other_chat = telegram_commands.handle_update(
        {
            "message": {
                "chat": {"id": 999, "type": "private"},
                "text": "/logbook",
            }
        },
        "12345",
    )
    group_chat = telegram_commands.handle_update(
        {
            "message": {
                "chat": {"id": 12345, "type": "group"},
                "text": "/logbook",
            }
        },
        "12345",
    )

    assert result == ("12345", "Logbook reply")
    assert other_chat is None
    assert group_chat is None


def test_get_updates_long_polls_and_advances_with_offset(monkeypatch):
    monkeypatch.setattr(telegram_transport.settings, "telegram_bot_token", "bot-token")
    requests_sent = []

    class Response:
        @staticmethod
        def raise_for_status():
            pass

        @staticmethod
        def json():
            return {"ok": True, "result": [{"update_id": 9}, "invalid"]}

    def get(url, params, timeout):
        requests_sent.append((url, params, timeout))
        return Response()

    monkeypatch.setattr(telegram_transport.requests, "get", get)

    updates = telegram_transport.get_updates(10)

    assert updates == [{"update_id": 9}]
    assert requests_sent[0][1]["offset"] == 10
    assert requests_sent[0][1]["timeout"] == telegram_transport.LONG_POLL_SECONDS
    assert requests_sent[0][2] > telegram_transport.LONG_POLL_SECONDS


def test_send_message_splits_long_replies_and_targets_configured_chat(monkeypatch):
    monkeypatch.setattr(telegram_transport.settings, "telegram_bot_token", "bot-token")
    sent = []

    class Response:
        @staticmethod
        def raise_for_status():
            pass

        @staticmethod
        def json():
            return {"ok": True}

    def post(url, json, timeout):
        sent.append((url, json, timeout))
        return Response()

    monkeypatch.setattr(telegram_transport.requests, "post", post)
    text = "é" * (telegram_transport.MESSAGE_LIMIT + 5)

    assert telegram_transport.send_message("12345", text) is True
    assert [len(item[1]["text"]) for item in sent] == [3900, 5]
    assert "bot-token/sendMessage" in sent[0][0]
    assert all(item[1]["chat_id"] == "12345" for item in sent)
    assert "".join(item[1]["text"] for item in sent) == text
