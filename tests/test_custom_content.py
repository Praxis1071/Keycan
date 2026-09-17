from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from keycan.data.database import Database
import keycan.data.database_runtime  # noqa: F401


def make_db(path: Path) -> Database:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE sources (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, relative_path TEXT NOT NULL UNIQUE DEFAULT '');
        CREATE TABLE lessons (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, legacy_metin_id INTEGER NOT NULL DEFAULT 0, title TEXT NOT NULL, text TEXT NOT NULL, FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE practice_results (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER NOT NULL, duration_seconds REAL NOT NULL, correct_chars INTEGER NOT NULL DEFAULT 0, wrong_chars INTEGER NOT NULL DEFAULT 0, wpm REAL NOT NULL DEFAULT 0, correct_words INTEGER NOT NULL DEFAULT 0, wrong_words INTEGER NOT NULL DEFAULT 0, words_per_minute REAL NOT NULL DEFAULT 0, characters_per_minute REAL NOT NULL DEFAULT 0);
        INSERT INTO sources VALUES (1, 'Hazır Ders', '');
        INSERT INTO lessons VALUES (1, 1, 1, 'Ders Test', 'hazır metin');
    """)
    connection.commit()
    connection.close()
    return Database(path)


def test_multiple_custom_groups_can_be_created_with_unique_legacy_paths(tmp_path: Path) -> None:
    db = make_db(tmp_path / "groups.db")
    try:
        first = db.create_custom_group("Python 101")
        second = db.create_custom_group("Linux 101")
        assert first != second
        paths = db.conn.execute(
            "SELECT relative_path FROM sources WHERE is_custom = 1 ORDER BY id"
        ).fetchall()
        assert len(paths) == 2
        assert len({row[0] for row in paths}) == 2
        assert all(row[0].startswith("custom://") for row in paths)
    finally:
        db.close()


def test_old_custom_groups_with_empty_paths_are_migrated(tmp_path: Path) -> None:
    db = make_db(tmp_path / "legacy.db")
    try:
        key = "legacy-custom-key"
        db.conn.execute(
            "INSERT INTO sources(id, display_name, relative_path, is_custom, is_deleted, custom_key) VALUES (?, ?, '', 1, 0, ?)",
            (10, "Eski Grup", key),
        )
        db.conn.commit()
        db.close()
        db = Database(tmp_path / "legacy.db")
        import keycan.data.database_runtime  # noqa: F401
        # Re-applying the runtime patch is unnecessary in normal app startup;
        # this assertion verifies the migration performed by the patched init.
        row = db.conn.execute(
            "SELECT relative_path FROM sources WHERE id = 10"
        ).fetchone()
        assert row and row[0] == "custom://legacy-custom-key"
    finally:
        db.close()


def test_any_group_reorder_preserves_text(tmp_path: Path) -> None:
    db = make_db(tmp_path / "custom.db")
    try:
        group = db.create_custom_group("Python 101")
        first = db.create_custom_lesson(group, "AAA")
        second = db.create_custom_lesson(group, "BBB")
        third = db.create_custom_lesson(group, "CCC")
        db.move_lesson(third, -1)
        db.move_lesson(third, -1)
        ordered = db.managed_lessons(group)
        assert [row[0] for row in ordered] == [third, first, second]
        assert [row[1] for row in ordered] == ["CCC", "AAA", "BBB"]

        built_in = db.managed_lessons(1)[0][0]
        db.update_lesson(built_in, "değiştirildi")
        assert db.lesson(built_in)[2] == "değiştirildi"
    finally:
        db.close()


def test_default_group_can_be_edited_and_deleted_without_losing_history(tmp_path: Path) -> None:
    db = make_db(tmp_path / "default.db")
    try:
        db.rename_group(1, "Benim Hazır Grubum")
        lesson = db.managed_lessons(1)[0][0]
        db.update_lesson(lesson, "değiştirilmiş metin")
        db.save_result(
            lesson, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        db.delete_group(1)
        assert db.sources() == [(1, "1. Python 101"),] if False else []
        assert db.conn.execute("SELECT COUNT(*) FROM practice_results").fetchone()[0] == 1
    finally:
        db.close()


def test_reset_all_then_restore_defaults(tmp_path: Path) -> None:
    db = make_db(tmp_path / "reset.db")
    try:
        group = db.create_custom_group("Kendi Grup")
        db.create_custom_lesson(group, "kendi metnim")
        db.update_lesson(1, "kullanıcının değiştirdiği içerik")
        groups, lessons = db.reset_all_content()
        assert (groups, lessons) == (2, 2)
        assert db.sources() == []
        restored_groups, restored_lessons = db.restore_defaults()
        assert (restored_groups, restored_lessons) == (1, 1)
        assert db.sources() == [(1, "1. Hazır Ders")]
        assert db.lesson(1)[2] == "hazır metin"
        assert not db.custom_groups()
    finally:
        db.close()


def test_restore_defaults_keeps_custom_content_out_and_history_intact(tmp_path: Path) -> None:
    db = make_db(tmp_path / "restore.db")
    try:
        custom_group = db.create_custom_group("Kendi Grup")
        custom_lesson = db.create_custom_lesson(custom_group, "kendi metnim")
        db.save_result(
            custom_lesson, 60, 2, 0,
            target_word_count=2, typed_word_count=2, total_characters=10,
            correct_characters=10, wrong_characters=0, words_per_minute=2,
            characters_per_minute=10, accuracy_percent=100,
        )
        db.rename_group(1, "Değişmiş Hazır Grup")
        db.update_lesson(1, "değişmiş hazır metin")
        restored_groups, restored_lessons = db.restore_defaults()
        assert (restored_groups, restored_lessons) == (1, 1)
        assert db.sources() == [(1, "1. Hazır Ders"), (2, "2. Kendi Grup")]
        assert db.lesson(1)[2] == "hazır metin"
        assert [row[1] for row in db.custom_lessons(custom_group)] == ["kendi metnim"]
        assert db.conn.execute("SELECT COUNT(*) FROM practice_results").fetchone()[0] == 1
    finally:
        db.close()


def test_backup_round_trip_restores_content_and_stats(tmp_path: Path) -> None:
    db = make_db(tmp_path / "source.db")
    try:
        group = db.create_custom_group("Yedek Grubu")
        lesson = db.create_custom_lesson(group, "yedek metni")
        db.save_result(
            lesson, 60, 4, 0,
            target_word_count=4, typed_word_count=4, total_characters=12,
            correct_characters=12, wrong_characters=0, words_per_minute=4,
            characters_per_minute=12, accuracy_percent=100,
        )
        backup = db.export_data()
    finally:
        db.close()
    restored = make_db(tmp_path / "restored.db")
    try:
        imported, skipped = restored.import_data(backup)
        assert imported == 2 and skipped == 0
        groups = restored.custom_groups()
        assert len(groups) == 1
        lessons = restored.custom_lessons(groups[0][0])
        assert [row[1] for row in lessons] == ["yedek metni"]
        assert restored.practice_statistics("Tümü")["practices"] == 1
        json.loads(restored.export_data())
    finally:
        restored.close()
