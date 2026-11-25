"""Telegram commands for viewing and editing the project's logbook defaults."""

from app import logbook_store
from app.logbook_store import LogbookField

FIELD_ALIASES: dict[str, LogbookField] = {
    "activity": "activity_log",
    "activity_log": "activity_log",
    "lesson": "lesson_learned",
    "lesson_learned": "lesson_learned",
    "obstacle": "obstacles",
    "obstacles": "obstacles",
}
FIELD_LABELS = {
    "activity_log": "Aktivitas",
    "lesson_learned": "Pelajaran",
    "obstacles": "Kendala",
}
MAX_FIELD_LENGTH = 3500

HELP_TEXT = (
    "Perintah logbook:\n"
    "/logbook — lihat semua entri, termasuk yang sudah digunakan\n"
    "/set activity_log <teks> — ubah fallback .env\n"
    "/set lesson_learned <teks> — ubah fallback .env\n"
    "/set obstacles <teks> — ubah fallback .env\n"
    "/clear <field> — kosongkan fallback .env setelah konfirmasi\n"
    "Alias field: activity, lesson, obstacle."
)


def handle_command(text: str) -> str | None:
    """Return a reply for a supported command; ignore ordinary chat messages."""
    if not isinstance(text, str) or not text.startswith("/"):
        return None

    parts = text.strip().split(maxsplit=2)
    command = parts[0][1:].split("@", 1)[0].lower()
    args = parts[1:]

    if command in ("help", "start"):
        return HELP_TEXT
    if command == "logbook":
        return _show_logbook()
    if command == "set":
        return _set_field(args)
    if command == "clear":
        return _clear_field(text.strip().split())
    return HELP_TEXT


def is_allowed_private_chat(chat: dict, allowed_chat_id: str) -> bool:
    return (
        chat.get("type") == "private"
        and bool(allowed_chat_id)
        and str(chat.get("id", "")) == str(allowed_chat_id)
    )


def handle_update(update: dict, allowed_chat_id: str) -> tuple[str, str] | None:
    """Return (chat_id, reply) only for commands from the configured private chat."""
    message = update.get("message")
    if not isinstance(message, dict):
        return None

    chat = message.get("chat")
    if not isinstance(chat, dict) or not is_allowed_private_chat(chat, allowed_chat_id):
        return None

    text = message.get("text")
    if not isinstance(text, str):
        return None

    reply = handle_command(text)
    if reply is None:
        return None
    return str(chat["id"]), reply


def _show_logbook() -> str:
    entries = logbook_store.get_logbook_entries()
    if entries is None:
        return "Tidak dapat membaca file logs_pool.json."

    fallback = logbook_store.get_logbook_fields()
    if fallback is None:
        return "Tidak dapat membaca file .env proyek."

    used_count = sum(
        1 for entry in entries if isinstance(entry, dict) and bool(entry.get("used", False))
    )
    sections = [
        (
            f"Semua logbook: {len(entries)} entri "
            f"({used_count} terpakai, {len(entries) - used_count} belum terpakai)."
        )
    ]
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            sections.append(f"\n#{index} — format entri tidak valid.")
            continue

        status = "TERPAKAI" if entry.get("used", False) else "BELUM DIPAKAI"
        used_at = entry.get("used_at")
        if isinstance(used_at, str) and used_at:
            status += f" — {used_at}"
        sections.append(f"\n#{index} — {status}")
        for field, label in FIELD_LABELS.items():
            value = entry.get(field)
            if not isinstance(value, str) or not value:
                value = "(kosong)"
            sections.append(f"{label}:\n{value}")

    sections.append("\nFallback .env (dipakai saat antrean logbook habis):")
    for field, label in FIELD_LABELS.items():
        value = fallback.get(field, "") or "(kosong)"
        sections.append(f"{label}:\n{value}")
    return "\n".join(sections)


def _set_field(args: list[str]) -> str:
    if not args:
        return "Format: /set <activity_log|lesson_learned|obstacles> <teks>"
    if len(args) == 1:
        return "Teks tidak boleh kosong. Gunakan /clear untuk mengosongkan field."

    field = FIELD_ALIASES.get(args[0].lower())
    if field is None:
        return "Field tidak dikenal. Gunakan activity_log, lesson_learned, atau obstacles."

    value = args[1].strip()
    if not value:
        return "Teks tidak boleh kosong. Gunakan /clear untuk mengosongkan field."
    if len(value) > MAX_FIELD_LENGTH:
        return f"Teks terlalu panjang; batasnya {MAX_FIELD_LENGTH} karakter."

    if not logbook_store.update_logbook_field(field, value):
        return "Gagal menyimpan ke file .env proyek."
    return f"{FIELD_LABELS[field]} berhasil diperbarui."


def _clear_field(parts: list[str]) -> str:
    if len(parts) not in (2, 3):
        return "Format: /clear <activity_log|lesson_learned|obstacles> [confirm]"

    field = FIELD_ALIASES.get(parts[1].lower())
    if field is None:
        return "Field tidak dikenal. Gunakan activity_log, lesson_learned, atau obstacles."
    if len(parts) == 2:
        return f"Untuk mengosongkan {FIELD_LABELS[field]}, kirim /clear {parts[1]} confirm."
    if parts[2].lower() != "confirm":
        return f"Konfirmasi tidak valid. Kirim /clear {parts[1]} confirm."

    if not logbook_store.update_logbook_field(field, ""):
        return "Gagal mengosongkan nilai di file .env proyek."
    return (
        f"{FIELD_LABELS[field]} berhasil dikosongkan. Isi kembali sebelum absen berikutnya; "
        "field kosong dapat membuat pengiriman logbook gagal."
    )
