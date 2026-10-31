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
        assert db.sources() == []
        assert db.conn.execute("SELECT COUNT(*) FROM practice_results").fetchone()[0] == 1
    finally:
        db.close()


def test_reset_all_then_restore_defaults(tmp_path: Path) -> None:
    db = make_db(tmp_path / "reset.db")
    try:
        group = db.create_custom_group("Kendi Grup")
        db.create_custom_lesson(group, "kendi metnim")
        db.rename_group(1, "Benim Ders Grubum")
        db.update_lesson(1, "kullanıcının değiştirdiği içerik")
        groups, lessons = db.reset_all_content()
        assert (groups, lessons) == (2, 2)
        assert db.sources() == []
        restored_groups, restored_lessons = db.restore_defaults()
        assert (restored_groups, restored_lessons) == (1, 1)
        assert db.sources() == [(1, "1. Benim Ders Grubum")]
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
        assert db.sources() == [(1, "1. Değişmiş Hazır Grup"), (2, "2. Kendi Grup")]
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
            wrong_letter_counts={"a": 2, "E": 1},
        )
        backup = db.export_data()
    finally:
        db.close()
    restored = make_db(tmp_path / "restored.db")
    try:
        imported, skipped = restored.import_data(backup)
        assert imported == 3 and skipped == 0
        groups = restored.custom_groups()
        assert len(groups) == 1
        lessons = restored.custom_lessons(groups[0][0])
        assert [row[1] for row in lessons] == ["yedek metni"]
        assert restored.practice_statistics("Tümü")["practices"] == 1
        assert restored.wrong_letter_statistics("Tümü") == [("a", 2), ("e", 1)]
        exported = json.loads(restored.export_data())
        assert json.loads(exported["practice_results"][0]["wrong_letter_counts"]) == {"a": 2, "e": 1}
    finally:
        restored.close()

def test_backup_round_trip_preserves_default_lesson_history(tmp_path: Path) -> None:
    source = make_db(tmp_path / "default-source.db")
    try:
        source.save_result(
            1, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        backup = json.loads(source.export_data())
        assert backup["practice_results"][0]["source_key"] == "default:1"
        assert backup["practice_results"][0]["lesson_key"] == "default:1"
    finally:
        source.close()

    target = make_db(tmp_path / "default-target.db")
    try:
        imported, skipped = target.import_data(json.dumps(backup))
        assert (imported, skipped) == (3, 0)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 1
        assert target.conn.execute(
            "SELECT lesson_id FROM practice_results"
        ).fetchone()[0] == 1
    finally:
        target.close()


def test_default_backup_does_not_overwrite_custom_group_with_same_id(tmp_path: Path) -> None:
    source = make_db(tmp_path / "collision-source.db")
    try:
        source.save_result(
            1, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        backup = source.export_data()
    finally:
        source.close()

    target = make_db(tmp_path / "collision-target.db")
    try:
        target.conn.execute(
            """UPDATE sources
               SET display_name = 'My custom group', relative_path = 'custom://collision',
                   is_custom = 1, custom_key = 'collision-key'
               WHERE id = 1"""
        )
        target.conn.execute("UPDATE lessons SET is_custom = 1 WHERE id = 1")
        target.conn.commit()

        imported, skipped = target.import_data(backup)
        assert (imported, skipped) == (1, 0)
        collision = target.conn.execute(
            "SELECT display_name, is_custom FROM sources WHERE id = 1"
        ).fetchone()
        assert collision == ("My custom group", 1)
        restored_default = target.conn.execute(
            "SELECT id FROM sources WHERE display_name = 'Hazır Ders' AND is_custom = 0"
        ).fetchone()
        assert restored_default is not None
        restored_lesson = target.conn.execute(
            "SELECT id FROM lessons WHERE source_id = ? AND is_custom = 0",
            (restored_default[0],),
        ).fetchone()
        assert restored_lesson is not None
        result_lesson = target.conn.execute(
            "SELECT lesson_id FROM practice_results"
        ).fetchone()
        assert result_lesson == restored_lesson
        assert target.import_data(backup) == (0, 1)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 1
    finally:
        target.close()

def test_backup_preserves_custom_lesson_inside_default_group(tmp_path: Path) -> None:
    source = make_db(tmp_path / "mixed-source.db")
    try:
        source.save_result(
            1, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        backup = json.loads(source.export_data())
        default_group = next(group for group in backup["groups"] if group["default_source_id"] == 1)
        lesson = default_group["lessons"][0]
        lesson["key"] = "custom-lesson-key"
        lesson["is_custom"] = True
        lesson["default_lesson_id"] = None
        lesson["text"] = "A custom lesson in a default group"
        backup["practice_results"][0]["lesson_key"] = "custom-lesson-key"
    finally:
        source.close()

    target = make_db(tmp_path / "mixed-target.db")
    try:
        imported, skipped = target.import_data(json.dumps(backup))
        assert (imported, skipped) == (1, 0)
        restored = target.conn.execute(
            "SELECT id, is_custom FROM lessons WHERE source_id = 1 AND text = ?",
            ("A custom lesson in a default group",),
        ).fetchone()
        assert restored is not None
        assert restored[1] == 1
        assert target.conn.execute(
            "SELECT lesson_id FROM practice_results"
        ).fetchone() == (restored[0],)
    finally:
        target.close()

def make_shifted_default_db(path: Path) -> Database:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY,
            display_name TEXT NOT NULL,
            relative_path TEXT NOT NULL UNIQUE DEFAULT ''
        );
        CREATE TABLE lessons (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            legacy_metin_id INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        CREATE TABLE practice_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            duration_seconds REAL NOT NULL,
            correct_chars INTEGER NOT NULL DEFAULT 0,
            wrong_chars INTEGER NOT NULL DEFAULT 0,
            wpm REAL NOT NULL DEFAULT 0,
            correct_words INTEGER NOT NULL DEFAULT 0,
            wrong_words INTEGER NOT NULL DEFAULT 0,
            words_per_minute REAL NOT NULL DEFAULT 0,
            characters_per_minute REAL NOT NULL DEFAULT 0
        );
        INSERT INTO sources VALUES (1, 'Other Default', 'default://1');
        INSERT INTO sources VALUES (2, 'Hazır Ders', 'default://2');
        INSERT INTO lessons VALUES (1, 1, 1, 'Other Lesson', 'other text');
        INSERT INTO lessons VALUES (2, 2, 1, 'Ders Test', 'hazır metin');
    """)
    connection.commit()
    connection.close()
    return Database(path)


def test_default_backup_maps_by_content_identity_when_numeric_ids_shift(tmp_path: Path) -> None:
    source = make_db(tmp_path / "identity-source.db")
    try:
        source.save_result(
            1, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        backup = source.export_data()
    finally:
        source.close()

    target = make_shifted_default_db(tmp_path / "identity-target.db")
    try:
        imported, skipped = target.import_data(backup)
        assert (imported, skipped) == (1, 0)
        assert target.conn.execute(
            "SELECT display_name FROM sources WHERE id = 1"
        ).fetchone() == ("Other Default",)
        assert target.conn.execute(
            "SELECT lesson_id FROM practice_results"
        ).fetchone() == (2,)
        assert target.import_data(backup) == (0, 1)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 1
    finally:
        target.close()


def test_legacy_backup_skips_ambiguous_name_based_lesson_mapping(tmp_path: Path) -> None:
    db = make_db(tmp_path / "ambiguous.db")
    try:
        db.conn.execute(
            """INSERT INTO sources(
                   display_name, relative_path, is_custom, is_deleted, custom_key
               ) VALUES ('Hazır Ders', 'default://duplicate', 0, 0, '')"""
        )
        duplicate_source = db.conn.execute(
            "SELECT id FROM sources WHERE relative_path = 'default://duplicate'"
        ).fetchone()[0]
        db.conn.execute(
            """INSERT INTO lessons(
                   source_id, legacy_metin_id, title, text,
                   is_custom, is_deleted, custom_order, custom_key
               ) VALUES (?, 1, 'Ders Test', 'başka metin', 0, 0, 0, '')""",
            (duplicate_source,),
        )
        db.conn.commit()
        backup = json.dumps({
            "format": "keycan-backup",
            "version": 1,
            "custom_groups": [],
            "practice_results": [{
                "completed_at": "2026-10-31 10:00:00",
                "duration_seconds": 60,
                "correct_words": 1,
                "wrong_words": 0,
                "words_per_minute": 1,
                "characters_per_minute": 5,
                "target_word_count": 1,
                "typed_word_count": 1,
                "total_characters": 5,
                "correct_characters": 5,
                "wrong_characters": 0,
                "accuracy_percent": 100,
                "wrong_letter_counts": {},
                "source_name": "Hazır Ders",
                "lesson_title": "Ders Test",
            }],
        })
        assert db.import_data(backup) == (0, 1)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 0
    finally:
        db.close()



def test_backup_round_trip_preserves_deleted_lesson_history(tmp_path: Path) -> None:
    source = make_db(tmp_path / "deleted-source.db")
    try:
        source.save_result(
            1, 60, 1, 0,
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        source.delete_lesson(1)
        backup = source.export_data()
        payload = json.loads(backup)
        assert payload["groups"][0]["lessons"][0]["is_deleted"] is True
    finally:
        source.close()

    target = make_db(tmp_path / "deleted-target.db")
    try:
        target.import_data(backup)
        assert target.conn.execute(
            "SELECT is_deleted FROM lessons WHERE id = 1"
        ).fetchone() == (1,)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 1
        assert target.practice_statistics("Tümü")["practices"] == 1
    finally:
        target.close()


def test_backup_session_uuids_keep_identical_sessions_and_prevent_reimport(tmp_path: Path) -> None:
    source = make_db(tmp_path / "session-source.db")
    try:
        metrics = dict(
            target_word_count=1, typed_word_count=1, total_characters=5,
            correct_characters=5, wrong_characters=0, words_per_minute=1,
            characters_per_minute=5, accuracy_percent=100,
        )
        source.save_result(1, 60, 1, 0, session_uuid="session-one", **metrics)
        source.save_result(1, 60, 1, 0, session_uuid="session-two", **metrics)
        backup = source.export_data()
        exported = json.loads(backup)
        assert exported["version"] == 3
        assert {item["session_uuid"] for item in exported["practice_results"]} == {
            "session-one", "session-two"
        }
    finally:
        source.close()

    target = make_db(tmp_path / "session-target.db")
    try:
        target.import_data(backup)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 2
        assert target.conn.execute(
            "SELECT COUNT(DISTINCT session_uuid) FROM practice_results"
        ).fetchone()[0] == 2

        target.import_data(backup)
        assert target.conn.execute(
            "SELECT COUNT(*) FROM practice_results"
        ).fetchone()[0] == 2
    finally:
        target.close()


def test_legacy_sessions_receive_stable_ids_during_migration(tmp_path: Path) -> None:
    path = tmp_path / "legacy-session.db"
    db = make_db(path)
    try:
        db.conn.execute(
            "INSERT INTO practice_results(lesson_id, duration_seconds) VALUES (1, 60)"
        )
        db.conn.commit()
    finally:
        db.close()

    migrated = make_db(path)
    try:
        session_uuid = migrated.conn.execute(
            "SELECT session_uuid FROM practice_results"
        ).fetchone()[0]
        assert isinstance(session_uuid, str) and session_uuid
        assert migrated.conn.execute(
            "PRAGMA index_list(practice_results)"
        ).fetchall()
    finally:
        migrated.close()
