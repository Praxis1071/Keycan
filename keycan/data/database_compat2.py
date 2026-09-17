"""Runtime compatibility layer for custom content and safe backup import."""

from __future__ import annotations

import json
from datetime import datetime

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key


def sources(self: Database) -> list[tuple[int, str]]:
    rows = self.conn.execute(
        "SELECT id, display_name, is_custom FROM sources WHERE is_deleted = 0"
    ).fetchall()
    visible = []
    for source_id, name, is_custom in rows:
        has_lessons = self.conn.execute(
            "SELECT 1 FROM lessons WHERE source_id = ? AND is_deleted = 0 LIMIT 1",
            (source_id,),
        ).fetchone()
        if has_lessons or is_custom:
            visible.append((source_id, clean_source_name(name), bool(is_custom)))
    visible.sort(key=lambda row: natural_sort_key(row[1]))
    result = []
    builtin_number = 0
    for source_id, name, is_custom in visible:
        if is_custom:
            result.append((source_id, name))
        else:
            builtin_number += 1
            result.append((source_id, self._display_source_name(name, builtin_number)))
    return result


def import_data(self: Database, raw: str) -> tuple[int, int]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Yedek dosyası geçerli JSON değil") from exc
    if not isinstance(payload, dict) or payload.get("format") != "keycan-backup" or payload.get("version") != 1:
        raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
    groups = payload.get("custom_groups", [])
    results = payload.get("practice_results", [])
    if not isinstance(groups, list) or not isinstance(results, list):
        raise ValueError("Yedek dosyasının yapısı geçersiz")

    lesson_map: dict[str, int] = {}
    self.conn.execute("BEGIN")
    try:
        for group in groups:
            if not isinstance(group, dict):
                raise ValueError("Ders grubu kaydı geçersiz")
            key = str(group.get("key", "")).strip()
            name = self._validate_group_name(str(group.get("name", "")))
            if not key:
                raise ValueError("Ders grubu kimliği eksik")
            existing = self.conn.execute("SELECT id FROM sources WHERE custom_key = ? AND is_custom = 1", (key,)).fetchone()
            if existing:
                source_id = int(existing[0])
                self.conn.execute("UPDATE sources SET display_name = ?, is_deleted = 0 WHERE id = ?", (name, source_id))
            else:
                source_id = int(self.conn.execute("INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key) VALUES (?, '', 1, 0, ?)", (name, key)).lastrowid)
            lessons = group.get("lessons", [])
            if not isinstance(lessons, list):
                raise ValueError("Ders grubu metin listesi geçersiz")
            for order, lesson in enumerate(lessons):
                if not isinstance(lesson, dict):
                    raise ValueError("Metin kaydı geçersiz")
                lesson_key = str(lesson.get("key", "")).strip()
                text = self._validate_text(str(lesson.get("text", "")))
                if not lesson_key:
                    raise ValueError("Metin kimliği eksik")
                existing_lesson = self.conn.execute("SELECT id FROM lessons WHERE custom_key = ? AND is_custom = 1", (lesson_key,)).fetchone()
                if existing_lesson:
                    lesson_id = int(existing_lesson[0])
                    self.conn.execute("UPDATE lessons SET source_id = ?, text = ?, title = 'Ders', custom_order = ?, is_deleted = 0 WHERE id = ?", (source_id, text, order, lesson_id))
                else:
                    lesson_id = int(self.conn.execute("INSERT INTO lessons(source_id, legacy_metin_id, title, text, is_custom, is_deleted, custom_order, custom_key) VALUES (?, 0, 'Ders', ?, 1, 0, ?, ?)", (source_id, text, order, lesson_key)).lastrowid)
                lesson_map[lesson_key] = lesson_id

        existing = {
            tuple(row) for row in self.conn.execute(
                "SELECT completed_at, lesson_id, duration_seconds, words_per_minute, typed_word_count, accuracy_percent FROM practice_results WHERE completed_at != ''"
            ).fetchall()
        }
        imported = skipped = 0
        for result in results:
            if not isinstance(result, dict):
                skipped += 1
                continue
            lesson_key = str(result.get("lesson_key", "")).strip()
            lesson_id = lesson_map.get(lesson_key) if lesson_key else None
            if lesson_id is None:
                source_name = clean_source_name(str(result.get("source_name", "")))
                lesson_title = str(result.get("lesson_title", ""))
                candidates = self.conn.execute(
                    "SELECT l.id, s.display_name, l.title FROM lessons l JOIN sources s ON s.id = l.source_id WHERE s.is_custom = 0 AND s.is_deleted = 0 AND l.is_deleted = 0"
                ).fetchall()
                for candidate_id, candidate_source, candidate_title in candidates:
                    if clean_source_name(candidate_source) == source_name and candidate_title == lesson_title:
                        lesson_id = int(candidate_id); break
            if lesson_id is None:
                skipped += 1; continue
            completed_at = str(result.get("completed_at", ""))
            try:
                datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                duration = float(result.get("duration_seconds", 0)); correct_words = int(result.get("correct_words", 0)); wrong_words = int(result.get("wrong_words", 0)); wpm = float(result.get("words_per_minute", 0)); cpm = float(result.get("characters_per_minute", 0)); target_words = int(result.get("target_word_count", 0)); typed_words = int(result.get("typed_word_count", 0)); total_chars = int(result.get("total_characters", 0)); correct_chars = int(result.get("correct_characters", 0)); wrong_chars = int(result.get("wrong_characters", 0)); accuracy = float(result.get("accuracy_percent", 0))
            except (TypeError, ValueError):
                skipped += 1; continue
            if min(duration, correct_words, wrong_words, wpm, cpm, target_words, typed_words, total_chars, correct_chars, wrong_chars, accuracy) < 0 or accuracy > 100 or correct_words + wrong_words != typed_words or total_chars != correct_chars + wrong_chars:
                skipped += 1; continue
            fingerprint = (completed_at, lesson_id, duration, wpm, typed_words, accuracy)
            if fingerprint in existing:
                continue
            self.conn.execute(
                """INSERT INTO practice_results(lesson_id, duration_seconds, correct_chars, wrong_chars, wpm, correct_words, wrong_words, words_per_minute, characters_per_minute, completed_at, source_name_snapshot, lesson_title_snapshot, target_word_count, typed_word_count, total_characters, correct_characters, wrong_characters, accuracy_percent)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (lesson_id, duration, correct_chars, wrong_chars, wpm, correct_words, wrong_words, wpm, cpm, completed_at, str(result.get("source_name", "")), str(result.get("lesson_title", "")), target_words, typed_words, total_chars, correct_chars, wrong_chars, accuracy),
            )
            existing.add(fingerprint); imported += 1
        self.conn.commit()
        return imported, skipped
    except Exception:
        self.conn.rollback()
        raise


Database.sources = sources
Database.import_data = import_data
