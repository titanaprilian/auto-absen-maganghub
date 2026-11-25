from app import telegram_commands


def test_logbook_includes_the_env_fallback(monkeypatch):
    monkeypatch.setattr(telegram_commands.logbook_store, "get_logbook_entries", lambda: [])
    monkeypatch.setattr(
        telegram_commands.logbook_store,
        "get_logbook_fields",
        lambda: {
            "activity_log": "Menyusun endpoint",
            "lesson_learned": "Memahami validasi",
            "obstacles": "Tidak ada",
        },
    )

    reply = telegram_commands.handle_command("/logbook") or ""

    assert "Semua logbook: 0 entri" in reply
    assert "Fallback .env" in reply
    assert "Menyusun endpoint" in reply
    assert "Memahami validasi" in reply
    assert "Tidak ada" in reply


def test_logbook_lists_used_and_unused_pool_entries(monkeypatch):
    monkeypatch.setattr(
        telegram_commands.logbook_store,
        "get_logbook_entries",
        lambda: [
            {
                "activity_log": "Log lama",
                "lesson_learned": "Pelajaran lama",
                "obstacles": "Kendala lama",
                "used": True,
                "used_at": "2026-11-20",
            },
            {
                "activity_log": "Log berikutnya",
                "lesson_learned": "Pelajaran berikutnya",
                "obstacles": "Tidak ada",
                "used": False,
            },
        ],
    )
    monkeypatch.setattr(
        telegram_commands.logbook_store,
        "get_logbook_fields",
        lambda: {"activity_log": "Fallback", "lesson_learned": "", "obstacles": ""},
    )

    reply = telegram_commands.handle_command("/logbook") or ""

    assert "Semua logbook: 2 entri (1 terpakai, 1 belum terpakai)" in reply
    assert "#1 — TERPAKAI — 2026-11-20" in reply
    assert "Log lama" in reply
    assert "#2 — BELUM DIPAKAI" in reply
    assert "Log berikutnya" in reply


def test_set_updates_only_requested_value_and_preserves_newlines(monkeypatch):
    stored = {}

    def update(field, value):
        stored[field] = value
        return True

    monkeypatch.setattr(telegram_commands.logbook_store, "update_logbook_field", update)
    reply = telegram_commands.handle_command(
        "/set@absen_bot activity_log Membuat API\nMenguji respons"
    ) or ""

    assert stored == {"activity_log": "Membuat API\nMenguji respons"}
    assert "berhasil diperbarui" in reply


def test_clear_requires_confirmation_before_emptying_field(monkeypatch):
    stored = {"obstacles": "Koneksi tidak stabil"}
    updates = []

    def update(field, value):
        updates.append((field, value))
        stored[field] = value
        return True

    monkeypatch.setattr(telegram_commands.logbook_store, "update_logbook_field", update)

    first_reply = telegram_commands.handle_command("/clear obstacle") or ""
    assert stored["obstacles"] == "Koneksi tidak stabil"
    assert updates == []
    assert "/clear obstacle confirm" in first_reply

    confirm_reply = telegram_commands.handle_command("/clear obstacle confirm") or ""
    assert stored["obstacles"] == ""
    assert updates == [("obstacles", "")]
    assert "berhasil dikosongkan" in confirm_reply


def test_unknown_field_does_not_write(monkeypatch):
    writes = []
    monkeypatch.setattr(
        telegram_commands.logbook_store,
        "update_logbook_field",
        lambda *args: writes.append(args) or True,
    )

    reply = telegram_commands.handle_command("/set password rahasia") or ""

    assert "Field tidak dikenal" in reply
    assert writes == []


def test_set_rejects_empty_and_overlong_values(monkeypatch):
    writes = []
    monkeypatch.setattr(
        telegram_commands.logbook_store,
        "update_logbook_field",
        lambda *args: writes.append(args) or True,
    )

    empty_reply = telegram_commands.handle_command("/set activity_log   ") or ""
    long_reply = telegram_commands.handle_command(
        "/set activity_log " + ("x" * (telegram_commands.MAX_FIELD_LENGTH + 1))
    ) or ""

    assert "tidak boleh kosong" in empty_reply
    assert "terlalu panjang" in long_reply
    assert writes == []


def test_ordinary_messages_are_ignored():
    assert telegram_commands.handle_command("Halo bot") is None
