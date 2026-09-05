from __future__ import annotations

import sqlite3
from pathlib import Path

from keycan.utils.text import clean_source_name, natural_sort_key


class Database:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self._migrate_results_schema()

    def _migrate_results_schema(self) -> None:
        columns = {
            row[1] for row in self.conn.execute("PRAGMA table_info(practice_results)")
        }
        additions = {
            "correct_words": "INTEGER NOT NULL DEFAULT 0",
            "wrong_words": "INTEGER NOT NULL DEFAULT 0",
            "words_per_minute": "REAL NOT NULL DEFAULT 0",
            "characters_per_minute": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.conn.execute(
                    f"ALTER TABLE practice_results ADD COLUMN {name} {definition}"
                )
        self.conn.commit()

    def sources(self) -> list[tuple[int, str]]:
        rows = self.conn.execute("SELECT id, display_name FROM sources").fetchall()
        cleaned = [(source_id, clean_source_name(name)) for source_id, name in rows]
        cleaned = [
            row
            for row in cleaned
            if self.conn.execute(
                "SELECT 1 FROM lessons WHERE source_id = ? LIMIT 1", (row[0],)
            ).fetchone()
        ]
        cleaned.sort(key=lambda row: natural_sort_key(row[1]))
        numbered: list[tuple[int, str]] = []
        for index, (source_id, name) in enumerate(cleaned, 1):
            numbered.append((source_id, self._display_source_name(name, index)))
        return numbered

    @staticmethod
    def _display_source_name(name: str, number: int) -> str:
        import re

        match = re.match(r"^\s*\d+\.\s*(.*)$", name)
        if match:
            return f"{number}. {match.group(1)}"
        return f"{number}. {name}"

    def lessons(self, source_id: int) -> list[tuple[int, str]]:
        rows = self.conn.execute(
            "SELECT id, title FROM lessons WHERE source_id = ? ORDER BY legacy_metin_id, id",
            (source_id,),
        ).fetchall()
        return [(lesson_id, f"Ders {index}") for index, (lesson_id, _) in enumerate(rows, 1)]

    def lesson(self, lesson_id: int) -> tuple[int, str, str]:
        row = self.conn.execute(
            "SELECT id, title, text FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        return row

    def save_result(self, lesson_id: int, duration: float, correct: int, wrong: int) -> None:
        self.conn.execute(
            """INSERT INTO practice_results(
                lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                correct_words, wrong_words, words_per_minute, characters_per_minute
            ) VALUES (?, ?, 0, 0, 0, ?, ?, 0, 0)""",
            (lesson_id, duration, correct, wrong),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
