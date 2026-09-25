from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from keycan.data.database import Database
import keycan.data.database_runtime  # noqa: F401
from keycan.services.progression import (
    badge_keys,
    level_for_xp,
    level_progress,
    session_xp,
    streaks,
)


def test_stage7_session_xp_and_levels() -> None:
    assert session_xp(
        duration_seconds=60,
        typed_word_count=20,
        words_per_minute=40,
        accuracy_percent=100,
    ) == 58
    assert session_xp(
        duration_seconds=60,
        typed_word_count=0,
        words_per_minute=100,
        accuracy_percent=100,
    ) == 0
    assert level_for_xp(0) == 1
    assert level_for_xp(100) == 2
    assert level_for_xp(299) == 2
    assert level_for_xp(300) == 3
    assert level_progress(125) == (2, 25, 200)


def test_stage7_streaks_use_distinct_calendar_days() -> None:
    today = date(2026, 9, 25)
    timestamps = [
        "2026-09-20 10:00:00",
        "2026-09-21 11:00:00",
        "2026-09-21 15:00:00",
        "2026-09-22 12:00:00",
        "2026-09-25 12:00:00",
    ]
    assert streaks(timestamps, today=today) == (1, 3)
    assert streaks(timestamps, today=today - timedelta(days=1))[0] == 0


def test_stage7_badges_are_derived_from_progress() -> None:
    unlocked = badge_keys(
        sessions=10,
        max_wpm=60,
        max_accuracy=98,
        max_duration_seconds=600,
        best_streak=7,
        xp=1000,
    )
    assert {
        "first_session", "ten_sessions", "speed_40", "speed_60",
        "accuracy_95", "accuracy_98", "long_session", "streak_7", "xp_1000",
    } <= unlocked
    assert "fifty_sessions" not in unlocked


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
            characters_per_minute REAL NOT NULL DEFAULT 0,
            completed_at TEXT NOT NULL DEFAULT '',
            source_name_snapshot TEXT NOT NULL DEFAULT '',
            lesson_title_snapshot TEXT NOT NULL DEFAULT '',
            target_word_count INTEGER NOT NULL DEFAULT 0,
            typed_word_count INTEGER NOT NULL DEFAULT 0,
            total_characters INTEGER NOT NULL DEFAULT 0,
            correct_characters INTEGER NOT NULL DEFAULT 0,
            wrong_characters INTEGER NOT NULL DEFAULT 0,
            accuracy_percent REAL NOT NULL DEFAULT 0,
            wrong_letter_counts TEXT NOT NULL DEFAULT '{}'
        );
        INSERT INTO sources VALUES (1, 'Test', '');
        INSERT INTO lessons VALUES (1, 1, 1, 'Ders', 'bir iki');
        """
    )
    connection.commit()
    connection.close()
    return Database(path)


def test_stage7_database_summary_is_local_and_derived(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "progress.db")
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)
        for completed_at, wpm, accuracy, duration in (
            (yesterday, 40, 100, 60),
            (today, 60, 98, 600),
        ):
            db.conn.execute(
                """INSERT INTO practice_results(
                    lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                    correct_words, wrong_words, words_per_minute,
                    characters_per_minute, completed_at, source_name_snapshot,
                    lesson_title_snapshot, target_word_count, typed_word_count,
                    total_characters, correct_characters, wrong_characters,
                    accuracy_percent, wrong_letter_counts
                ) VALUES (1, ?, 10, 0, ?, ?, 0, ?, 1, ?, 'Test', 'Ders',
                          20, 20, 20, 20, 0, ?, '{}')""",
                (
                    duration,
                    wpm,
                    20,
                    wpm,
                    completed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    accuracy,
                ),
            )
        db.conn.commit()
        summary = db.progression_summary()
        assert summary["sessions"] == 2
        assert summary["xp"] == 116
        assert summary["max_wpm"] == 60
        assert summary["max_accuracy"] == 100
        assert summary["max_duration_seconds"] == 600
        assert summary["current_streak"] == 2
        assert summary["best_streak"] == 2
    finally:
        db.close()
