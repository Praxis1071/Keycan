from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from keycan.data.database import Database


def _seed_database(path: Path) -> Database:
    db = Database(path)
    db.conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            display_name TEXT NOT NULL,
            relative_path TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            legacy_metin_id INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            text TEXT NOT NULL
        );
        """
    )
    db.conn.execute(
        "INSERT INTO sources(id, display_name) VALUES (1, '1. Test Kaynak')"
    )
    db.conn.execute(
        "INSERT INTO lessons(id, source_id, legacy_metin_id, title, text) VALUES (1, 1, 1, 'Test Ders', 'bir iki üç')"
    )
    db.conn.commit()
    return db


def test_stage5_statistics_totals_and_error_analysis(tmp_path: Path) -> None:
    db = _seed_database(tmp_path / "stats.db")
    try:
        db.save_result(
            1, 60, 2, 1,
            target_word_count=3, typed_word_count=3,
            total_characters=15, correct_characters=13, wrong_characters=2,
            words_per_minute=3, characters_per_minute=15, accuracy_percent=66.666,
            wrong_letter_counts={"a": 2, "e": 1},
        )
        db.save_result(
            1, 120, 4, 0,
            target_word_count=4, typed_word_count=4,
            total_characters=20, correct_characters=20, wrong_characters=0,
            words_per_minute=2, characters_per_minute=10, accuracy_percent=100,
            wrong_letter_counts={"e": 2},
        )

        stats = db.practice_statistics("Son 7 Gün")
        assert stats["practices"] == 2
        assert stats["total_words"] == 7
        assert stats["total_characters"] == 35
        assert stats["wrong_words"] == 1
        assert stats["accuracy_percent"] > 80

        assert db.wrong_letter_statistics("Son 7 Gün", 2) == [("e", 3), ("a", 2)]
        lesson = db.lesson_performance("Son 7 Gün")
        assert lesson[0]["sessions"] == 2
        assert lesson[0]["typed_words"] == 7

        comparison = db.period_comparison("Son 7 Gün")
        assert comparison["current"]["sessions"] == 2
    finally:
        db.close()


def test_stage5_period_comparison_uses_previous_equivalent_window(tmp_path: Path) -> None:
    db = _seed_database(tmp_path / "comparison.db")
    try:
        now = datetime.now(timezone.utc)
        current = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        previous = (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
        for completed_at, wpm in ((current, 5.0), (previous, 2.0)):
            db.conn.execute(
                """INSERT INTO practice_results(
                    lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                    correct_words, wrong_words, words_per_minute, characters_per_minute,
                    completed_at, source_name_snapshot, lesson_title_snapshot,
                    target_word_count, typed_word_count, total_characters,
                    correct_characters, wrong_characters, accuracy_percent, wrong_letter_counts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    1, 60, 1, 0, wpm, 5, 0, wpm, 0,
                    completed_at, "Test Kaynak", "Test Ders",
                    5, 5, 5, 5, 0, 100, "{}",
                ),
            )
        db.conn.commit()
        comparison = db.period_comparison("Son 7 Gün")
        assert comparison["current"]["sessions"] == 1
        assert comparison["previous"]["sessions"] == 1
        assert comparison["current"]["wpm"] == 5
        assert comparison["previous"]["wpm"] == 2
    finally:
        db.close()
