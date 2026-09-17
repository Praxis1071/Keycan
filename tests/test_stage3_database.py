from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from keycan.data.database import Database


def _make_db(path: Path) -> Database:
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
            characters_per_minute REAL NOT NULL DEFAULT 0
        );
        INSERT INTO sources VALUES (1, 'Test Kaynak', '');
        INSERT INTO lessons VALUES (10, 1, 1, 'Ders Test', 'Bir iki üç dört');
        """
    )
    connection.commit()
    connection.close()
    return Database(path)


def _insert_result(db: Database, completed_at: datetime, correct: int, wrong: int, wpm: float) -> None:
    db.conn.execute(
        """INSERT INTO practice_results(
               lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
               correct_words, wrong_words, words_per_minute, characters_per_minute,
               completed_at, source_name_snapshot, lesson_title_snapshot,
               target_word_count, typed_word_count, total_characters,
               correct_characters, wrong_characters, accuracy_percent
           ) VALUES (10, 60, 10, 1, ?, ?, ?, ?, ?, ?, 'Test Kaynak', 'Ders Test',
                     5, ?, 11, 10, 1, ?)""",
        (
            wpm,
            correct,
            wrong,
            wpm,
            wpm * 5,
            completed_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            correct + wrong,
            correct / (correct + wrong) * 100.0,
        ),
    )
    db.conn.commit()


def test_stage3_statistics_are_real_and_period_aware(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "stats.db")
    try:
        now = datetime.now().astimezone()
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)

        _insert_result(db, today, 9, 1, 30.0)
        _insert_result(db, yesterday, 4, 1, 20.0)

        daily = db.practice_statistics("Günlük")
        assert daily["practices"] == 1
        assert daily["total_words"] == 10
        assert daily["correct_words"] == 9
        assert daily["wrong_words"] == 1
        assert daily["accuracy_percent"] == 90.0
        assert daily["speed_points"] == [("12:00", 30.0)]
        assert len(daily["history"]) == 1

        all_stats = db.practice_statistics("Tümü")
        assert all_stats["practices"] == 2
        assert all_stats["total_words"] == 15
        assert all_stats["correct_words"] == 13
        assert all_stats["wrong_words"] == 2
        assert round(float(all_stats["accuracy_percent"]), 2) == 86.67
        assert len(all_stats["history"]) == 2
    finally:
        db.close()


def test_stage3_legacy_empty_timestamps_are_not_fabricated(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "legacy.db")
    try:
        db.conn.execute(
            """INSERT INTO practice_results(
                   lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                   correct_words, wrong_words, words_per_minute, characters_per_minute
               ) VALUES (10, 60, 4, 0, 4, 4, 0, 4, 4)"""
        )
        db.conn.commit()
        stats = db.practice_statistics("Tümü")
        assert stats["practices"] == 0
        assert stats["history"] == []
    finally:
        db.close()


def test_stage3_activity_is_grouped_by_local_calendar_year(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "activity.db")
    try:
        now = datetime.now().astimezone()
        this_year = now.year
        previous_year = this_year - 1
        current = now.replace(month=9, day=10, hour=12, minute=0, second=0, microsecond=0)
        previous = current.replace(year=previous_year)
        _insert_result(db, current, 9, 1, 30.0)
        _insert_result(db, previous, 8, 2, 20.0)

        years = db.practice_activity_years()
        assert this_year in years
        assert previous_year in years

        current_days = db.practice_activity(this_year)
        previous_days = db.practice_activity(previous_year)
        assert len(current_days) == 1
        assert len(previous_days) == 1
        assert current_days[0]["sessions"] == 1
        assert previous_days[0]["sessions"] == 1
        assert current_days[0]["accuracy_percent"] == 90.0
        assert previous_days[0]["accuracy_percent"] == 80.0
    finally:
        db.close()
