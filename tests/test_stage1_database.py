from __future__ import annotations

import sqlite3
from pathlib import Path
import tempfile

from keycan.data.database import Database


def test_stage1_save_result_and_migration() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "test.db"
        connection = sqlite3.connect(path)
        connection.executescript(
            """
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY,
                display_name TEXT NOT NULL,
                relative_path TEXT NOT NULL DEFAULT ''
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
                characters_per_minute REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(lesson_id) REFERENCES lessons(id)
            );
            INSERT INTO sources(id, display_name) VALUES (1, '1. Test Kaynak');
            INSERT INTO lessons(id, source_id, legacy_metin_id, title, text)
                VALUES (10, 1, 1, 'Test Ders', 'Bir iki üç dört');
            """
        )
        connection.commit()
        connection.close()

        db = Database(path)
        columns = {row[1] for row in db.conn.execute("PRAGMA table_info(practice_results)")}
        required = {
            "completed_at",
            "source_name_snapshot",
            "lesson_title_snapshot",
            "target_word_count",
            "typed_word_count",
            "total_characters",
            "correct_characters",
            "wrong_characters",
            "accuracy_percent",
        }
        assert required <= columns
        assert db.lessons(1) == [(10, "Ders 1")]

        db.save_result(
            10,
            60.0,
            3,
            1,
            target_word_count=4,
            typed_word_count=4,
            total_characters=16,
            correct_characters=15,
            wrong_characters=1,
            words_per_minute=4.0,
            characters_per_minute=16.0,
            accuracy_percent=75.0,
        )

        row = db.conn.execute(
            """SELECT lesson_id, duration_seconds, correct_words, wrong_words,
                      words_per_minute, characters_per_minute, completed_at,
                      source_name_snapshot, lesson_title_snapshot,
                      target_word_count, typed_word_count, total_characters,
                      correct_characters, wrong_characters, accuracy_percent
               FROM practice_results ORDER BY id DESC LIMIT 1"""
        ).fetchone()
        assert row is not None
        assert row[0:6] == (10, 60.0, 3, 1, 4.0, 16.0)
        assert row[6] != ""
        assert row[7:] == ("Test Kaynak", "Test Ders", 4, 4, 16, 15, 1, 75.0)
        db.close()


def test_stage1_rejects_inconsistent_metrics(tmp_path: Path) -> None:
    path = tmp_path / "test.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE sources (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL);
        CREATE TABLE lessons (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            legacy_metin_id INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            text TEXT NOT NULL
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
        INSERT INTO sources VALUES (1, 'Test');
        INSERT INTO lessons VALUES (1, 1, 1, 'Ders', 'Metin');
        """
    )
    connection.commit()
    connection.close()

    db = Database(path)
    try:
        db.save_result(
            1,
            60.0,
            2,
            0,
            target_word_count=2,
            typed_word_count=1,
            total_characters=4,
            correct_characters=4,
            wrong_characters=0,
            words_per_minute=1.0,
            characters_per_minute=4.0,
            accuracy_percent=200.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Tutarsız çalışma ölçümleri kabul edildi")
    finally:
        db.close()
