import json

from dotenv import dotenv_values

from app.logbook_store import (
    get_logbook_entries,
    get_logbook_fields,
    update_logbook_field,
)


def test_get_reads_only_the_three_logbook_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'ACTIVITY_LOG="Aktivitas"\n'
        'LESSON_LEARNED="Pelajaran"\n'
        'OBSTACLES="Kendala"\n'
        'TELEGRAM_BOT_TOKEN="keep-this-setting"\n',
        encoding="utf-8",
    )

    assert get_logbook_fields(env_file) == {
        "activity_log": "Aktivitas",
        "lesson_learned": "Pelajaran",
        "obstacles": "Kendala",
    }


def test_get_logbook_entries_includes_entries_already_used(tmp_path):
    pool_file = tmp_path / "logs_pool.json"
    entries = [
        {"activity_log": "Old entry", "used": True, "used_at": "2026-11-20"},
        {"activity_log": "Available entry", "used": False},
    ]
    pool_file.write_text(json.dumps(entries), encoding="utf-8")

    assert get_logbook_entries(pool_file) == entries


def test_update_preserves_other_env_values_and_multiline_content(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Preserve comments and unrelated settings\n"
        'ACTIVITY_LOG="Aktivitas lama"\n'
        "LESSON_LEARNED=Pelajaran_lama\n"
        "OBSTACLES=Kendala_lama\n"
        'TELEGRAM_BOT_TOKEN="keep-this-setting"\n',
        encoding="utf-8",
    )
    value = 'Baris pertama: "kutipan"\nBaris kedua'

    assert update_logbook_field("activity_log", value, env_file)

    values = dotenv_values(env_file)
    assert values["ACTIVITY_LOG"] == value
    assert values["LESSON_LEARNED"] == "Pelajaran_lama"
    assert values["OBSTACLES"] == "Kendala_lama"
    assert values["TELEGRAM_BOT_TOKEN"] == "keep-this-setting"
    assert env_file.read_text(encoding="utf-8").startswith(
        "# Preserve comments and unrelated settings\n"
    )


def test_update_can_clear_a_value_and_rejects_unknown_fields(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OBSTACLES=Kendala\n", encoding="utf-8")

    assert update_logbook_field("obstacles", "", env_file)
    assert get_logbook_fields(env_file)["obstacles"] == ""
    assert not update_logbook_field("password", "secret", env_file)


def test_missing_env_file_fails_without_creating_it(tmp_path):
    env_file = tmp_path / ".env"

    assert get_logbook_fields(env_file) is None
    assert not update_logbook_field("activity_log", "Aktivitas", env_file)
    assert not env_file.exists()
