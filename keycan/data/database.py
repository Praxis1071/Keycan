from __future__ import annotations

import json
import math
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from keycan.utils.text import clean_source_name, natural_sort_key


class Database:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self._migrate_results_schema()
        self._migrate_user_content_schema()

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
            "wrong_letter_counts": "TEXT NOT NULL DEFAULT '{}'",
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

    def _migrate_user_content_schema(self) -> None:
        source_columns = {
            row[1] for row in self.conn.execute("PRAGMA table_info(sources)")
        }
        lesson_columns = {
            row[1] for row in self.conn.execute("PRAGMA table_info(lessons)")
        }
        source_additions = {
            "is_custom": "INTEGER NOT NULL DEFAULT 0",
            "is_deleted": "INTEGER NOT NULL DEFAULT 0",
            "custom_key": "TEXT NOT NULL DEFAULT ''",
        }
        lesson_additions = {
            "is_custom": "INTEGER NOT NULL DEFAULT 0",
            "is_deleted": "INTEGER NOT NULL DEFAULT 0",
            "custom_order": "INTEGER NOT NULL DEFAULT 0",
            "custom_key": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in source_additions.items():
            if name not in source_columns:
                self.conn.execute(f"ALTER TABLE sources ADD COLUMN {name} {definition}")
        for name, definition in lesson_additions.items():
            if name not in lesson_columns:
                self.conn.execute(f"ALTER TABLE lessons ADD COLUMN {name} {definition}")
        self.conn.commit()

    def sources(self) -> list[tuple[int, str]]:
        rows = self.conn.execute(
            "SELECT id, display_name FROM sources WHERE is_deleted = 0"
        ).fetchall()
        cleaned = [(source_id, clean_source_name(name)) for source_id, name in rows]
        cleaned = [
            row
            for row in cleaned
            if self.conn.execute(
                "SELECT 1 FROM lessons WHERE source_id = ? AND is_deleted = 0 LIMIT 1",
                (row[0],),
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
        custom = self.conn.execute(
            "SELECT is_custom FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        if custom and custom[0]:
            rows = self.conn.execute(
                """SELECT id FROM lessons
                   WHERE source_id = ? AND is_deleted = 0
                   ORDER BY custom_order, id""",
                (source_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """SELECT id FROM lessons
                   WHERE source_id = ? AND is_deleted = 0
                   ORDER BY legacy_metin_id, id""",
                (source_id,),
            ).fetchall()
        return [(lesson_id, f"Ders {index}") for index, (lesson_id,) in enumerate(rows, 1)]

    def lesson(self, lesson_id: int) -> tuple[int, str, str]:
        row = self.conn.execute(
            "SELECT id, title, text FROM lessons WHERE id = ? AND is_deleted = 0",
            (lesson_id,),
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        return row

    def lesson_context(self, lesson_id: int) -> tuple[str, str]:
        row = self.conn.execute(
            """SELECT sources.display_name, lessons.title
               FROM lessons
               JOIN sources ON sources.id = lessons.source_id
               WHERE lessons.id = ? AND lessons.is_deleted = 0 AND sources.is_deleted = 0""",
            (lesson_id,),
        ).fetchone()
        if not row:
            raise ValueError("Ders bağlamı bulunamadı")
        source_name, lesson_title = row
        if not lesson_title or lesson_title == "Ders":
            custom = self.conn.execute(
                "SELECT is_custom FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if custom and custom[0]:
                position = self._custom_lesson_position(lesson_id)
                lesson_title = f"Ders {position}"
        return clean_source_name(source_name), lesson_title

    def _custom_lesson_position(self, lesson_id: int) -> int:
        row = self.conn.execute(
            "SELECT source_id, custom_order FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        source_id, custom_order = row
        count = self.conn.execute(
            """SELECT COUNT(*) FROM lessons
               WHERE source_id = ? AND is_custom = 1 AND is_deleted = 0
                 AND (custom_order < ? OR (custom_order = ? AND id <= ?))""",
            (source_id, custom_order, custom_order, lesson_id),
        ).fetchone()[0]
        return int(count)

    def custom_groups(self) -> list[tuple[int, str, str]]:
        return self.conn.execute(
            """SELECT id, display_name, custom_key FROM sources
               WHERE is_custom = 1 AND is_deleted = 0
               ORDER BY display_name COLLATE NOCASE, id"""
        ).fetchall()

    def custom_lessons(self, source_id: int) -> list[tuple[int, str, str, int]]:
        return self.conn.execute(
            """SELECT id, text, custom_key, custom_order FROM lessons
               WHERE source_id = ? AND is_custom = 1 AND is_deleted = 0
               ORDER BY custom_order, id""",
            (source_id,),
        ).fetchall()

    @staticmethod
    def _validate_group_name(name: str) -> str:
        value = " ".join(name.strip().split())
        if not value:
            raise ValueError("Ders grubu adı boş olamaz")
        if len(value) > 80:
            raise ValueError("Ders grubu adı en fazla 80 karakter olabilir")
        return value

    @staticmethod
    def _validate_text(text: str) -> str:
        value = text.strip()
        if not value:
            raise ValueError("Metin boş olamaz")
        if len(value) > 100_000:
            raise ValueError("Metin en fazla 100.000 karakter olabilir")
        return value

    def create_custom_group(self, name: str) -> int:
        name = self._validate_group_name(name)
        key = uuid.uuid4().hex
        cursor = self.conn.execute(
            """INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key)
               VALUES (?, '', 1, 0, ?)""",
            (name, key),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def rename_custom_group(self, source_id: int, name: str) -> None:
        name = self._validate_group_name(name)
        cursor = self.conn.execute(
            "UPDATE sources SET display_name = ? WHERE id = ? AND is_custom = 1 AND is_deleted = 0",
            (name, source_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Ders grubu bulunamadı")
        self.conn.commit()

    def delete_custom_group(self, source_id: int) -> None:
        cursor = self.conn.execute(
            "UPDATE sources SET is_deleted = 1 WHERE id = ? AND is_custom = 1 AND is_deleted = 0",
            (source_id,),
        )
        if cursor.rowcount != 1:
            raise ValueError("Ders grubu bulunamadı")
        self.conn.execute(
            "UPDATE lessons SET is_deleted = 1 WHERE source_id = ? AND is_custom = 1",
            (source_id,),
        )
        self.conn.commit()

    def create_custom_lesson(self, source_id: int, text: str) -> int:
        text = self._validate_text(text)
        valid = self.conn.execute(
            "SELECT 1 FROM sources WHERE id = ? AND is_custom = 1 AND is_deleted = 0",
            (source_id,),
        ).fetchone()
        if not valid:
            raise ValueError("Kullanıcı ders grubu bulunamadı")
        order = self.conn.execute(
            "SELECT COALESCE(MAX(custom_order), -1) + 1 FROM lessons WHERE source_id = ? AND is_custom = 1 AND is_deleted = 0",
            (source_id,),
        ).fetchone()[0]
        key = uuid.uuid4().hex
        cursor = self.conn.execute(
            """INSERT INTO lessons(source_id, legacy_metin_id, title, text, is_custom, is_deleted, custom_order, custom_key)
               VALUES (?, 0, 'Ders', ?, 1, 0, ?, ?)""",
            (source_id, text, order, key),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def update_custom_lesson(self, lesson_id: int, text: str) -> None:
        text = self._validate_text(text)
        cursor = self.conn.execute(
            "UPDATE lessons SET text = ? WHERE id = ? AND is_custom = 1 AND is_deleted = 0",
            (text, lesson_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Metin bulunamadı")
        self.conn.commit()

    def delete_custom_lesson(self, lesson_id: int) -> None:
        row = self.conn.execute(
            "SELECT source_id FROM lessons WHERE id = ? AND is_custom = 1 AND is_deleted = 0",
            (lesson_id,),
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE id = ?", (lesson_id,))
        self.conn.commit()
        self._normalize_custom_order(int(row[0]))

    def move_custom_lesson(self, lesson_id: int, direction: int) -> None:
        if direction not in (-1, 1):
            raise ValueError("Geçersiz sıralama yönü")
        rows = self.conn.execute(
            """SELECT id FROM lessons
               WHERE source_id = (SELECT source_id FROM lessons WHERE id = ?)
                 AND is_custom = 1 AND is_deleted = 0
               ORDER BY custom_order, id""",
            (lesson_id,),
        ).fetchall()
        ids = [row[0] for row in rows]
        if lesson_id not in ids:
            raise ValueError("Metin bulunamadı")
        index = ids.index(lesson_id)
        target = index + direction
        if target < 0 or target >= len(ids):
            return
        ids[index], ids[target] = ids[target], ids[index]
        self.conn.execute("BEGIN")
        try:
            for order, item_id in enumerate(ids):
                self.conn.execute(
                    "UPDATE lessons SET custom_order = ? WHERE id = ?",
                    (order, item_id),
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _normalize_custom_order(self, source_id: int) -> None:
        rows = self.conn.execute(
            "SELECT id FROM lessons WHERE source_id = ? AND is_custom = 1 AND is_deleted = 0 ORDER BY custom_order, id",
            (source_id,),
        ).fetchall()
        for order, (lesson_id,) in enumerate(rows):
            self.conn.execute("UPDATE lessons SET custom_order = ? WHERE id = ?", (order, lesson_id))
        self.conn.commit()

    def _practice_export_rows(self) -> list[dict[str, object]]:
        rows = self.conn.execute(
            """SELECT r.completed_at, r.duration_seconds, r.correct_words, r.wrong_words,
                      r.words_per_minute, r.characters_per_minute, r.target_word_count,
                      r.typed_word_count, r.total_characters, r.correct_characters,
                      r.wrong_characters, r.accuracy_percent, r.wrong_letter_counts, r.source_name_snapshot,
                      r.lesson_title_snapshot, s.custom_key, l.custom_key
               FROM practice_results r
               LEFT JOIN lessons l ON l.id = r.lesson_id
               LEFT JOIN sources s ON s.id = l.source_id
               WHERE r.completed_at != ''
               ORDER BY r.completed_at, r.rowid"""
        ).fetchall()
        fields = (
            "completed_at", "duration_seconds", "correct_words", "wrong_words",
            "words_per_minute", "characters_per_minute", "target_word_count",
            "typed_word_count", "total_characters", "correct_characters",
            "wrong_characters", "accuracy_percent", "wrong_letter_counts", "source_name", "lesson_title",
            "source_key", "lesson_key",
        )
        return [dict(zip(fields, row)) for row in rows]

    def export_data(self) -> str:
        groups = []
        for source_id, name, source_key in self.custom_groups():
            lessons = [
                {
                    "key": key,
                    "text": text,
                    "order": order,
                }
                for _lesson_id, text, key, order in self.custom_lessons(source_id)
            ]
            groups.append({"key": source_key, "name": name, "lessons": lessons})
        payload = {
            "format": "keycan-backup",
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "custom_groups": groups,
            "practice_results": self._practice_export_rows(),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def reset_statistics(self) -> int:
        cursor = self.conn.execute("DELETE FROM practice_results")
        self.conn.commit()
        return cursor.rowcount

    def import_data(self, raw: str) -> tuple[int, int]:
        payload = json.loads(raw)
        if payload.get("format") != "keycan-backup" or payload.get("version") != 1:
            raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
        groups = payload.get("custom_groups", [])
        results = payload.get("practice_results", [])
        if not isinstance(groups, list) or not isinstance(results, list):
            raise ValueError("Yedek dosyasının yapısı geçersiz")

        group_map: dict[str, int] = {}
        lesson_map: dict[str, int] = {}
        self.conn.execute("BEGIN")
        try:
            for group in groups:
                key = str(group.get("key", ""))
                name = self._validate_group_name(str(group.get("name", "")))
                if not key:
                    raise ValueError("Ders grubu kimliği eksik")
                existing = self.conn.execute(
                    "SELECT id FROM sources WHERE custom_key = ? AND is_custom = 1",
                    (key,),
                ).fetchone()
                if existing:
                    source_id = int(existing[0])
                    self.conn.execute(
                        "UPDATE sources SET display_name = ?, is_deleted = 0 WHERE id = ?",
                        (name, source_id),
                    )
                else:
                    source_id = int(self.conn.execute(
                        "INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key) VALUES (?, '', 1, 0, ?)",
                        (name, key),
                    ).lastrowid)
                group_map[key] = source_id
                imported_lessons = group.get("lessons", [])
                if not isinstance(imported_lessons, list):
                    raise ValueError("Ders grubu metin listesi geçersiz")
                for order, lesson in enumerate(imported_lessons):
                    lesson_key = str(lesson.get("key", ""))
                    text = self._validate_text(str(lesson.get("text", "")))
                    if not lesson_key:
                        raise ValueError("Metin kimliği eksik")
                    existing_lesson = self.conn.execute(
                        "SELECT id FROM lessons WHERE custom_key = ? AND is_custom = 1",
                        (lesson_key,),
                    ).fetchone()
                    if existing_lesson:
                        lesson_id = int(existing_lesson[0])
                        self.conn.execute(
                            "UPDATE lessons SET source_id = ?, text = ?, title = 'Ders', custom_order = ?, is_deleted = 0 WHERE id = ?",
                            (source_id, text, order, lesson_id),
                        )
                    else:
                        lesson_id = int(self.conn.execute(
                            """INSERT INTO lessons(source_id, legacy_metin_id, title, text, is_custom, is_deleted, custom_order, custom_key)
                               VALUES (?, 0, 'Ders', ?, 1, 0, ?, ?)""",
                            (source_id, text, order, lesson_key),
                        ).lastrowid)
                    lesson_map[lesson_key] = lesson_id

            imported = 0
            skipped = 0
            for result in results:
                source_key = str(result.get("source_key", ""))
                lesson_key = str(result.get("lesson_key", ""))
                lesson_id = lesson_map.get(lesson_key) if lesson_key else None
                if lesson_id is None:
                    source_name = str(result.get("source_name", ""))
                    lesson_title = str(result.get("lesson_title", ""))
                    row = self.conn.execute(
                        """SELECT l.id FROM lessons l JOIN sources s ON s.id = l.source_id
                           WHERE s.is_deleted = 0 AND l.is_deleted = 0
                             AND clean_source_name(s.display_name) = ? AND l.title = ?
                           LIMIT 1""",
                        (clean_source_name(source_name), lesson_title),
                    ).fetchone()
                    if row:
                        lesson_id = int(row[0])
                if lesson_id is None:
                    skipped += 1
                    continue
                completed_at = str(result.get("completed_at", ""))
                datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                self.conn.execute(
                    """INSERT INTO practice_results(
                        lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                        correct_words, wrong_words, words_per_minute, characters_per_minute,
                        completed_at, source_name_snapshot, lesson_title_snapshot,
                        target_word_count, typed_word_count, total_characters,
                        correct_characters, wrong_characters, accuracy_percent, wrong_letter_counts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        lesson_id, float(result.get("duration_seconds", 0)), 0, 0,
                        float(result.get("words_per_minute", 0)),
                        int(result.get("correct_words", 0)), int(result.get("wrong_words", 0)),
                        float(result.get("words_per_minute", 0)), float(result.get("characters_per_minute", 0)),
                        completed_at, str(result.get("source_name", "")), str(result.get("lesson_title", "")),
                        int(result.get("target_word_count", 0)), int(result.get("typed_word_count", 0)),
                        int(result.get("total_characters", 0)), int(result.get("correct_characters", 0)),
                        int(result.get("wrong_characters", 0)), float(result.get("accuracy_percent", 0)),
                        json.dumps(result.get("wrong_letter_counts", {}), ensure_ascii=False),
                    ),
                )
                imported += 1
            self.conn.commit()
            return imported, skipped
        except Exception:
            self.conn.rollback()
            raise

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
        wrong_letter_counts: dict[str, int] | None = None,
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
            "wrong_letter_counts": wrong_letter_counts or {},
        }
        numeric_metrics = {key: value for key, value in metrics.items() if key != "wrong_letter_counts"}
        if any(not math.isfinite(value) or value < 0 for value in numeric_metrics.values()):
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
                correct_characters, wrong_characters, accuracy_percent, wrong_letter_counts
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                CURRENT_TIMESTAMP, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?
            )""",
            (
                lesson_id, duration, correct_characters, wrong_characters, words_per_minute,
                correct, wrong, words_per_minute, characters_per_minute,
                source_name, lesson_title, target_word_count, typed_word_count,
                total_characters, correct_characters, wrong_characters, accuracy_percent,
                json.dumps(wrong_letter_counts or {}, ensure_ascii=False),
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
        rows = self.conn.execute(
            "SELECT completed_at FROM practice_results WHERE completed_at != ''"
        ).fetchall()
        return sorted(
            {self._parse_completed_at(value).year for (value,) in rows},
            reverse=True,
        )

    def practice_activity(self, year: int) -> list[dict[str, object]]:
        if year < 1:
            raise ValueError("Yıl geçerli olmalıdır")
        local_tz = datetime.now().astimezone().tzinfo
        start = datetime(year, 1, 1, tzinfo=local_tz)
        end = datetime(year + 1, 1, 1, tzinfo=local_tz)
        rows = self.conn.execute(
            """SELECT completed_at, duration_seconds, typed_word_count,
                      correct_words, words_per_minute
               FROM practice_results
               WHERE completed_at != '' AND completed_at >= ? AND completed_at < ?
               ORDER BY completed_at ASC""",
            (self._utc_sql_value(start), self._utc_sql_value(end)),
        ).fetchall()
        daily: dict[object, dict[str, float]] = {}
        for row in rows:
            completed = self._parse_completed_at(row[0])
            day = completed.date()
            bucket = daily.setdefault(day, {"sessions": 0.0, "duration_seconds": 0.0, "words": 0.0, "correct_words": 0.0, "speed_total": 0.0})
            bucket["sessions"] += 1
            bucket["duration_seconds"] += float(row[1])
            bucket["words"] += int(row[2])
            bucket["correct_words"] += int(row[3])
            bucket["speed_total"] += float(row[4])
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
        now_local = datetime.now().astimezone()
        start_local = self._period_start(period, now_local)
        query = """SELECT id, completed_at, source_name_snapshot, lesson_title_snapshot,
                          duration_seconds, correct_words, wrong_words,
                          typed_word_count, words_per_minute
                   FROM practice_results WHERE completed_at != ''"""
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
                bucket, label = completed, completed.strftime("%H:%M")
            elif period in {"Haftalık", "Aylık"}:
                bucket, label = completed.date(), completed.strftime("%d %b")
            else:
                bucket, label = (completed.year, completed.month), completed.strftime("%b %Y")
            speed_buckets.setdefault((bucket, label), []).append(float(row[8]))
        speed_points = [
            (label, sum(values) / len(values))
            for (_bucket, label), values in sorted(speed_buckets.items(), key=lambda item: item[0][0])
        ]
        accuracy_buckets: dict[object, list[float]] = {}
        for row in reversed(rows):
            completed = self._parse_completed_at(row[1])
            if period == "Günlük":
                bucket, label = completed, completed.strftime("%H:%M")
            elif period in {"Haftalık", "Aylık"}:
                bucket, label = completed.date(), completed.strftime("%d %b")
            else:
                bucket, label = (completed.year, completed.month), completed.strftime("%b %Y")
            typed = int(row[7])
            accuracy_buckets.setdefault((bucket, label), []).append(
                int(row[5]) / typed * 100.0 if typed else 0.0
            )
        accuracy_points = [
            (label, sum(values) / len(values))
            for (_bucket, label), values in sorted(accuracy_buckets.items(), key=lambda item: item[0][0])
        ]
        history = [
            {
                "completed_at": self._parse_completed_at(row[1]),
                "source_name": row[2],
                "lesson_title": row[3],
                "duration_seconds": float(row[4]),
                "typed_word_count": int(row[7]),
                "accuracy_percent": int(row[5]) / int(row[7]) * 100.0 if int(row[7]) else 0.0,
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
            "accuracy_points": accuracy_points,
            "history": history,
        }

    def wrong_letter_statistics(self, period: str = "Tümü", limit: int = 10) -> list[tuple[str, int]]:
        stats: dict[str, int] = {}
        start_local = self._period_start(period, datetime.now().astimezone())
        query = "SELECT wrong_letter_counts FROM practice_results WHERE completed_at != ''"
        params: tuple[str, ...] = ()
        if start_local is not None:
            query += " AND completed_at >= ?"
            params = (self._utc_sql_value(start_local),)
        for (raw,) in self.conn.execute(query, params).fetchall():
            try:
                values = json.loads(raw or "{}")
            except json.JSONDecodeError:
                continue
            for letter, count in values.items():
                if isinstance(letter, str) and isinstance(count, int):
                    stats[letter] = stats.get(letter, 0) + count
        return sorted(stats.items(), key=lambda item: (-item[1], item[0]))[:max(1, limit)]

    def lesson_performance(self, period: str = "Tümü") -> list[dict[str, object]]:
        start_local = self._period_start(period, datetime.now().astimezone())
        query = """SELECT lesson_title_snapshot, source_name_snapshot, COUNT(*),
                          SUM(duration_seconds), SUM(typed_word_count),
                          SUM(correct_words), AVG(words_per_minute)
                   FROM practice_results WHERE completed_at != ''"""
        params: tuple[str, ...] = ()
        if start_local is not None:
            query += " AND completed_at >= ?"
            params = (self._utc_sql_value(start_local),)
        query += " GROUP BY source_name_snapshot, lesson_title_snapshot ORDER BY COUNT(*) DESC, lesson_title_snapshot COLLATE NOCASE"
        rows = self.conn.execute(query, params).fetchall()
        return [{"source_name": r[1], "lesson_title": r[0], "sessions": int(r[2]),
                 "duration_seconds": float(r[3] or 0), "typed_words": int(r[4] or 0),
                 "accuracy_percent": int(r[5] or 0) / int(r[4] or 1) * 100.0,
                 "average_wpm": float(r[6] or 0)} for r in rows]

    def period_comparison(self, period: str) -> dict[str, object]:
        now = datetime.now().astimezone()
        if period not in {"Günlük", "Haftalık", "Aylık", "Yıllık"}:
            raise ValueError("Karşılaştırma için geçerli bir dönem seçilmelidir")
        current_start = self._period_start(period, now)
        if period == "Günlük":
            previous_start = current_start - timedelta(days=1)
        elif period == "Haftalık":
            previous_start = current_start - timedelta(days=7)
        elif period == "Aylık":
            previous_start = (current_start.replace(day=1) - timedelta(days=1)).replace(day=1)
        else:
            previous_start = current_start.replace(year=current_start.year - 1)
        def aggregate(start: datetime, end: datetime) -> dict[str, float]:
            rows = self.conn.execute(
                "SELECT duration_seconds, typed_word_count, correct_words, words_per_minute FROM practice_results WHERE completed_at >= ? AND completed_at < ?",
                (self._utc_sql_value(start), self._utc_sql_value(end)),
            ).fetchall()
            sessions = len(rows)
            words = sum(int(r[1]) for r in rows)
            correct = sum(int(r[2]) for r in rows)
            return {"sessions": sessions, "duration_seconds": sum(float(r[0]) for r in rows),
                    "wpm": sum(float(r[3]) for r in rows) / sessions if sessions else 0.0,
                    "accuracy": correct / words * 100.0 if words else 0.0}
        return {"current": aggregate(current_start, now), "previous": aggregate(previous_start, current_start)}

    def close(self) -> None:
        self.conn.close()
