from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta, timezone
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
            "completed_at": "TEXT NOT NULL DEFAULT ''",
            "source_name_snapshot": "TEXT NOT NULL DEFAULT ''",
            "lesson_title_snapshot": "TEXT NOT NULL DEFAULT ''",
            "target_word_count": "INTEGER NOT NULL DEFAULT 0",
            "typed_word_count": "INTEGER NOT NULL DEFAULT 0",
            "total_characters": "INTEGER NOT NULL DEFAULT 0",
            "correct_characters": "INTEGER NOT NULL DEFAULT 0",
            "wrong_characters": "INTEGER NOT NULL DEFAULT 0",
            "accuracy_percent": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.conn.execute(
                    f"ALTER TABLE practice_results ADD COLUMN {name} {definition}"
                )

        self.conn.execute(
            """UPDATE practice_results
               SET source_name_snapshot = COALESCE(
                       (SELECT sources.display_name
                        FROM lessons
                        JOIN sources ON sources.id = lessons.source_id
                        WHERE lessons.id = practice_results.lesson_id), '')
               WHERE source_name_snapshot = ''"""
        )
        self.conn.execute(
            """UPDATE practice_results
               SET lesson_title_snapshot = COALESCE(
                       (SELECT lessons.title
                        FROM lessons
                        WHERE lessons.id = practice_results.lesson_id), '')
               WHERE lesson_title_snapshot = ''"""
        )
        self.conn.execute(
            """UPDATE practice_results
               SET typed_word_count = correct_words + wrong_words
               WHERE typed_word_count = 0 AND (correct_words > 0 OR wrong_words > 0)"""
        )
        self.conn.execute(
            """UPDATE practice_results
               SET accuracy_percent =
                   CASE
                       WHEN correct_words + wrong_words > 0
                       THEN correct_words * 100.0 / (correct_words + wrong_words)
                       ELSE 0
                   END
               WHERE accuracy_percent = 0
                 AND (correct_words > 0 OR wrong_words > 0)"""
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

    def lesson_context(self, lesson_id: int) -> tuple[str, str]:
        row = self.conn.execute(
            """SELECT sources.display_name, lessons.title
               FROM lessons
               JOIN sources ON sources.id = lessons.source_id
               WHERE lessons.id = ?""",
            (lesson_id,),
        ).fetchone()
        if not row:
            raise ValueError("Ders bağlamı bulunamadı")
        source_name, lesson_title = row
        return clean_source_name(source_name), lesson_title

    def save_result(
        self,
        lesson_id: int,
        duration: float,
        correct: int,
        wrong: int,
        *,
        target_word_count: int,
        typed_word_count: int,
        total_characters: int,
        correct_characters: int,
        wrong_characters: int,
        words_per_minute: float,
        characters_per_minute: float,
        accuracy_percent: float,
    ) -> None:
        metrics = {
            "duration": duration,
            "correct": correct,
            "wrong": wrong,
            "target_word_count": target_word_count,
            "typed_word_count": typed_word_count,
            "total_characters": total_characters,
            "correct_characters": correct_characters,
            "wrong_characters": wrong_characters,
            "words_per_minute": words_per_minute,
            "characters_per_minute": characters_per_minute,
            "accuracy_percent": accuracy_percent,
        }
        if any(not math.isfinite(value) or value < 0 for value in metrics.values()):
            raise ValueError("Çalışma ölçümleri geçerli ve negatif olmayan değerler olmalıdır")
        if correct + wrong != typed_word_count:
            raise ValueError("Doğru ve yanlış kelime toplamı yazılan kelime sayısıyla eşleşmiyor")
        if total_characters != correct_characters + wrong_characters:
            raise ValueError("Karakter ölçümleri tutarsız")
        if accuracy_percent > 100:
            raise ValueError("Doğruluk yüzdesi 100'ü aşamaz")

        source_name, lesson_title = self.lesson_context(lesson_id)
        self.conn.execute(
            """INSERT INTO practice_results(
                lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                correct_words, wrong_words, words_per_minute, characters_per_minute,
                completed_at, source_name_snapshot, lesson_title_snapshot,
                target_word_count, typed_word_count, total_characters,
                correct_characters, wrong_characters, accuracy_percent
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                CURRENT_TIMESTAMP, ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )""",
            (
                lesson_id,
                duration,
                correct_characters,
                wrong_characters,
                words_per_minute,
                correct,
                wrong,
                words_per_minute,
                characters_per_minute,
                source_name,
                lesson_title,
                target_word_count,
                typed_word_count,
                total_characters,
                correct_characters,
                wrong_characters,
                accuracy_percent,
            ),
        )
        self.conn.commit()

    @staticmethod
    def _period_start(period: str, now_local: datetime) -> datetime | None:
        if period == "Günlük":
            return now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "Haftalık":
            start = now_local - timedelta(days=now_local.weekday())
            return start.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "Aylık":
            return now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period == "Yıllık":
            return now_local.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        if period == "Tümü":
            return None
        raise ValueError(f"Bilinmeyen istatistik dönemi: {period}")

    @staticmethod
    def _utc_sql_value(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _parse_completed_at(value: str) -> datetime:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=timezone.utc).astimezone()

    def practice_activity_years(self) -> list[int]:
        """Return calendar years that contain real, timestamped practice records."""
        rows = self.conn.execute(
            """SELECT DISTINCT substr(completed_at, 1, 4) AS year
               FROM practice_results
               WHERE completed_at != ''
               ORDER BY year DESC"""
        ).fetchall()
        years: list[int] = []
        for (value,) in rows:
            try:
                year = int(value)
            except (TypeError, ValueError):
                continue
            if year >= 1:
                years.append(year)
        return years

    def practice_activity(self, year: int) -> list[dict[str, object]]:
        """Return daily activity aggregates for one local calendar year."""
        if year < 1:
            raise ValueError("Yıl geçerli olmalıdır")
        start = datetime(year, 1, 1, tzinfo=datetime.now().astimezone().tzinfo)
        end = datetime(year + 1, 1, 1, tzinfo=start.tzinfo)
        rows = self.conn.execute(
            """SELECT completed_at, duration_seconds, typed_word_count,
                      correct_words, wrong_words, words_per_minute
               FROM practice_results
               WHERE completed_at != ?
                 AND completed_at >= ?
                 AND completed_at < ?
               ORDER BY completed_at ASC""",
            ("", self._utc_sql_value(start), self._utc_sql_value(end)),
        ).fetchall()

        daily: dict[object, dict[str, float]] = {}
        for row in rows:
            completed = self._parse_completed_at(row[0])
            day = completed.date()
            bucket = daily.setdefault(
                day,
                {"sessions": 0.0, "duration_seconds": 0.0, "words": 0.0, "correct_words": 0.0, "speed_total": 0.0},
            )
            bucket["sessions"] += 1
            bucket["duration_seconds"] += float(row[1])
            bucket["words"] += int(row[2])
            bucket["correct_words"] += int(row[3])
            bucket["speed_total"] += float(row[5])

        return [
            {
                "date": day,
                "sessions": int(values["sessions"]),
                "duration_seconds": values["duration_seconds"],
                "words": int(values["words"]),
                "accuracy_percent": values["correct_words"] / values["words"] * 100.0 if values["words"] else 0.0,
                "average_speed": values["speed_total"] / values["sessions"] if values["sessions"] else 0.0,
            }
            for day, values in sorted(daily.items())
        ]

    def practice_statistics(self, period: str = "Haftalık") -> dict[str, object]:
        """Return real practice aggregates for the requested local-calendar period."""
        now_local = datetime.now().astimezone()
        start_local = self._period_start(period, now_local)

        query = """SELECT id, completed_at, source_name_snapshot, lesson_title_snapshot,
                          duration_seconds, correct_words, wrong_words,
                          typed_word_count, words_per_minute
                   FROM practice_results
                   WHERE completed_at != ''"""
        parameters: tuple[str, ...] = ()
        if start_local is not None:
            query += " AND completed_at >= ?"
            parameters = (self._utc_sql_value(start_local),)
        query += " ORDER BY completed_at DESC, id DESC"

        rows = self.conn.execute(query, parameters).fetchall()
        practices = len(rows)
        total_duration = sum(float(row[4]) for row in rows)
        total_words = sum(int(row[7]) for row in rows)
        total_correct = sum(int(row[5]) for row in rows)
        total_wrong = sum(int(row[6]) for row in rows)
        accuracy = total_correct / total_words * 100.0 if total_words else 0.0

        speed_buckets: dict[object, list[float]] = {}
        for row in reversed(rows):
            completed = self._parse_completed_at(row[1])
            if period == "Günlük":
                bucket = completed
                label = completed.strftime("%H:%M")
            elif period in {"Haftalık", "Aylık"}:
                bucket = completed.date()
                label = completed.strftime("%d %b")
            else:
                bucket = (completed.year, completed.month)
                label = completed.strftime("%b %Y")
            speed_buckets.setdefault((bucket, label), []).append(float(row[8]))

        speed_points = [
            (label, sum(values) / len(values))
            for (_bucket, label), values in sorted(speed_buckets.items(), key=lambda item: item[0][0])
        ]

        history = [
            {
                "completed_at": self._parse_completed_at(row[1]),
                "source_name": row[2],
                "lesson_title": row[3],
                "duration_seconds": float(row[4]),
                "typed_word_count": int(row[7]),
                "accuracy_percent": (
                    int(row[5]) / int(row[7]) * 100.0 if int(row[7]) else 0.0
                ),
                "words_per_minute": float(row[8]),
            }
            for row in rows[:50]
        ]

        return {
            "practices": practices,
            "duration_seconds": total_duration,
            "total_words": total_words,
            "correct_words": total_correct,
            "wrong_words": total_wrong,
            "accuracy_percent": accuracy,
            "speed_points": speed_points,
            "history": history,
        }

    def close(self) -> None:
        self.conn.close()
