"""Runtime compatibility and user-content management for Keycan."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key

_ORIGINAL_INIT = Database.__init__


def _custom_relative_path(source_id: int, custom_key: str = "") -> str:
    """Return a unique legacy path for a custom source.

    Older Keycan databases used an empty relative_path for every custom group,
    but that column is UNIQUE in the original schema.  New custom groups must
    therefore use a stable, non-empty placeholder path.
    """
    key = custom_key.strip() or uuid.uuid4().hex
    return f"custom://{key}"


def _migrate_custom_relative_paths(self: Database) -> None:
    """Repair old custom groups that all used relative_path=''."""
    rows = self.conn.execute(
        """SELECT id, custom_key FROM sources
           WHERE is_custom = 1 AND (relative_path = '' OR relative_path IS NULL)
           ORDER BY id"""
    ).fetchall()
    changed = False
    for source_id, custom_key in rows:
        key = str(custom_key or "").strip() or uuid.uuid4().hex
        self.conn.execute(
            "UPDATE sources SET custom_key = ?, relative_path = ? WHERE id = ?",
            (key, _custom_relative_path(source_id, key), source_id),
        )
        changed = True
    if changed:
        self.conn.commit()


def _ensure_default_snapshot(self: Database) -> None:
    _migrate_custom_relative_paths(self)
    self.conn.execute(
        """CREATE TABLE IF NOT EXISTS default_content_sources (
               source_id INTEGER PRIMARY KEY,
               display_name TEXT NOT NULL,
               relative_path TEXT NOT NULL,
               custom_key TEXT NOT NULL DEFAULT ''
           )"""
    )
    self.conn.execute(
        """CREATE TABLE IF NOT EXISTS default_content_lessons (
               lesson_id INTEGER PRIMARY KEY,
               source_id INTEGER NOT NULL,
               legacy_metin_id INTEGER NOT NULL DEFAULT 0,
               title TEXT NOT NULL,
               text TEXT NOT NULL,
               custom_order INTEGER NOT NULL DEFAULT 0
           )"""
    )
    if self.conn.execute("SELECT COUNT(*) FROM default_content_sources").fetchone()[0] == 0:
        source_rows = self.conn.execute(
            """SELECT id, display_name, relative_path, custom_key
               FROM sources WHERE is_custom = 0 ORDER BY id"""
        ).fetchall()
        lesson_rows = self.conn.execute(
            """SELECT id, source_id, legacy_metin_id, title, text, custom_order
               FROM lessons WHERE is_custom = 0
               ORDER BY source_id, legacy_metin_id, id"""
        ).fetchall()
        for row in source_rows:
            self.conn.execute("INSERT INTO default_content_sources VALUES (?,?,?,?)", row)
        for row in lesson_rows:
            self.conn.execute("INSERT INTO default_content_lessons VALUES (?,?,?,?,?,?)", row)
        self.conn.commit()


def _init(self: Database, path):
    _ORIGINAL_INIT(self, path)
    _ensure_default_snapshot(self)


def _sources(self: Database):
    rows = self.conn.execute(
        """SELECT id, display_name, is_custom FROM sources
           WHERE is_deleted = 0 ORDER BY display_name COLLATE NOCASE, id"""
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
    return [
        (source_id, self._display_source_name(name, index))
        for index, (source_id, name, _is_custom) in enumerate(visible, 1)
    ]


def _lessons(self: Database, source_id: int):
    rows = self.conn.execute(
        """SELECT id FROM lessons
           WHERE source_id = ? AND is_deleted = 0
           ORDER BY custom_order, legacy_metin_id, id""",
        (source_id,),
    ).fetchall()
    return [(lesson_id, f"Ders {index}") for index, (lesson_id,) in enumerate(rows, 1)]


def _custom_lesson_position(self: Database, lesson_id: int) -> int:
    row = self.conn.execute(
        "SELECT source_id, custom_order FROM lessons WHERE id = ?",
        (lesson_id,),
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    source_id, order = row
    return int(
        self.conn.execute(
            """SELECT COUNT(*) FROM lessons
               WHERE source_id = ? AND is_deleted = 0
                 AND (custom_order < ? OR (custom_order = ? AND id <= ?))""",
            (source_id, order, order, lesson_id),
        ).fetchone()[0]
    )


def _managed_groups(self: Database):
    return self.conn.execute(
        """SELECT id, display_name, custom_key, is_custom FROM sources
           WHERE is_deleted = 0
           ORDER BY display_name COLLATE NOCASE, id"""
    ).fetchall()


def _managed_lessons(self: Database, source_id: int):
    return self.conn.execute(
        """SELECT id, text, custom_key, custom_order, is_custom FROM lessons
           WHERE source_id = ? AND is_deleted = 0
           ORDER BY custom_order, legacy_metin_id, id""",
        (source_id,),
    ).fetchall()


def _rename_group(self: Database, source_id: int, name: str) -> None:
    name = self._validate_group_name(name)
    if self.conn.execute(
        "UPDATE sources SET display_name = ? WHERE id = ? AND is_deleted = 0",
        (name, source_id),
    ).rowcount != 1:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.commit()


def _delete_group(self: Database, source_id: int) -> None:
    if self.conn.execute(
        "UPDATE sources SET is_deleted = 1 WHERE id = ? AND is_deleted = 0",
        (source_id,),
    ).rowcount != 1:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE source_id = ?", (source_id,))
    self.conn.commit()


def _create_custom_group(self: Database, name: str) -> int:
    name = self._validate_group_name(name)
    key = uuid.uuid4().hex
    relative_path = _custom_relative_path(0, key)
    cursor = self.conn.execute(
        """INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key)
           VALUES (?, ?, 1, 0, ?)""",
        (name, relative_path, key),
    )
    self.conn.commit()
    return int(cursor.lastrowid)


def _create_lesson(self: Database, source_id: int, text: str) -> int:
    text = self._validate_text(text)
    if not self.conn.execute(
        "SELECT 1 FROM sources WHERE id = ? AND is_deleted = 0", (source_id,)
    ).fetchone():
        raise ValueError("Ders grubu bulunamadı")
    order = self.conn.execute(
        """SELECT COALESCE(MAX(custom_order), -1) + 1 FROM lessons
           WHERE source_id = ? AND is_deleted = 0""",
        (source_id,),
    ).fetchone()[0]
    key = uuid.uuid4().hex
    lesson_id = int(
        self.conn.execute(
            """INSERT INTO lessons(
                   source_id, legacy_metin_id, title, text,
                   is_custom, is_deleted, custom_order, custom_key
               ) VALUES (?, 0, 'Ders', ?, 1, 0, ?, ?)""",
            (source_id, text, order, key),
        ).lastrowid
    self.conn.commit()
    return lesson_id


def _update_lesson(self: Database, lesson_id: int, text: str) -> None:
    text = self._validate_text(text)
    if self.conn.execute(
        "UPDATE lessons SET text = ? WHERE id = ? AND is_deleted = 0",
        (text, lesson_id),
    ).rowcount != 1:
        raise ValueError("Metin bulunamadı")
    self.conn.commit()


def _delete_lesson(self: Database, lesson_id: int) -> None:
    row = self.conn.execute(
        "SELECT source_id FROM lessons WHERE id = ? AND is_deleted = 0", (lesson_id,)
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE id = ?", (lesson_id,))
    self.conn.commit()
    _normalize_order(self, int(row[0]))


def _move_lesson(self: Database, lesson_id: int, direction: int) -> None:
    if direction not in (-1, 1):
        raise ValueError("Geçersiz sıralama yönü")
    row = self.conn.execute(
        "SELECT source_id FROM lessons WHERE id = ? AND is_deleted = 0", (lesson_id,)
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    source_id = int(row[0])
    ids = [
        r[0]
        for r in self.conn.execute(
            """SELECT id FROM lessons
               WHERE source_id = ? AND is_deleted = 0
               ORDER BY custom_order, legacy_metin_id, id""",
            (source_id,),
        ).fetchall()
    ]
    index = ids.index(lesson_id)
    target = index + direction
    if target < 0 or target >= len(ids):
        return
    ids[index], ids[target] = ids[target], ids[index]
    self.conn.execute("BEGIN")
    try:
        for order, item_id in enumerate(ids):
            self.conn.execute("UPDATE lessons SET custom_order = ? WHERE id = ?", (order, item_id))
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise


def _normalize_order(self: Database, source_id: int) -> None:
    rows = self.conn.execute(
        """SELECT id FROM lessons WHERE source_id = ? AND is_deleted = 0
           ORDER BY custom_order, legacy_metin_id, id""",
        (source_id,),
    ).fetchall()
    for order, (lesson_id,) in enumerate(rows):
        self.conn.execute("UPDATE lessons SET custom_order = ? WHERE id = ?", (order, lesson_id))
    self.conn.commit()


def _reset_all_content(self: Database):
    _ensure_default_snapshot(self)
    groups = int(self.conn.execute("SELECT COUNT(*) FROM sources WHERE is_deleted = 0").fetchone()[0])
    lessons = int(self.conn.execute("SELECT COUNT(*) FROM lessons WHERE is_deleted = 0").fetchone()[0])
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE is_deleted = 0")
    self.conn.execute("UPDATE sources SET is_deleted = 1 WHERE is_deleted = 0")
    self.conn.commit()
    return groups, lessons


def _restore_defaults(self: Database):
    _ensure_default_snapshot(self)
    source_rows = self.conn.execute(
        "SELECT source_id, display_name, relative_path, custom_key FROM default_content_sources ORDER BY source_id"
    ).fetchall()
    lesson_rows = self.conn.execute(
        """SELECT lesson_id, source_id, legacy_metin_id, title, text, custom_order
           FROM default_content_lessons ORDER BY source_id, custom_order, lesson_id"""
    ).fetchall()
    self.conn.execute("BEGIN")
    try:
        for source_id, name, path, key in source_rows:
            self.conn.execute(
                """UPDATE sources
                   SET display_name = ?, relative_path = ?, custom_key = ?,
                       is_custom = 0, is_deleted = 0
                   WHERE id = ?""",
                (name, path, key, source_id),
            )
        ids = [row[0] for row in source_rows]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            self.conn.execute(
                f"UPDATE lessons SET is_deleted = 1 WHERE source_id IN ({placeholders})",
                tuple(ids),
            )
        for lesson_id, source_id, legacy_id, title, text, order in lesson_rows:
            self.conn.execute(
                """UPDATE lessons SET source_id = ?, legacy_metin_id = ?, title = ?, text = ?,
                   is_custom = 0, is_deleted = 0, custom_order = ? WHERE id = ?""",
                (source_id, legacy_id, title, text, order, lesson_id),
            )
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise
    return len(source_rows), len(lesson_rows)


def _export_data(self: Database) -> str:
    groups = []
    for source_id, name, key, is_custom in self._managed_groups():
        group_key = key or f"default:{source_id}"
        lessons = []
        for lesson_id, text, lesson_key, order, lesson_custom in self._managed_lessons(source_id):
            lessons.append({
                "key": lesson_key or f"default:{lesson_id}",
                "text": text,
                "order": order,
                "default_lesson_id": None if lesson_custom else lesson_id,
            })
        groups.append({
            "key": group_key,
            "name": name,
            "lessons": lessons,
            "is_custom": bool(is_custom),
            "default_source_id": None if is_custom else source_id,
        })
    rows = self.conn.execute(
        """SELECT r.completed_at, r.duration_seconds, r.correct_words, r.wrong_words,
                  r.words_per_minute, r.characters_per_minute, r.target_word_count,
                  r.typed_word_count, r.total_characters, r.correct_characters,
                  r.wrong_characters, r.accuracy_percent, r.source_name_snapshot,
                  r.lesson_title_snapshot, s.custom_key, l.custom_key, l.id, s.id
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
        "wrong_characters", "accuracy_percent", "source_name", "lesson_title",
        "source_key", "lesson_key", "lesson_id", "source_id",
    )
    return json.dumps(
        {"format": "keycan-backup", "version": 2,
         "exported_at": datetime.now().astimezone().isoformat(),
         "groups": groups,
         "practice_results": [dict(zip(fields, row)) for row in rows]},
        ensure_ascii=False,
        indent=2,
    )


def _import_data(self: Database, raw: str):
    payload = json.loads(raw)
    if payload.get("format") != "keycan-backup" or payload.get("version") not in (1, 2):
        raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
    groups = payload.get("groups", payload.get("custom_groups", []))
    results = payload.get("practice_results", [])
    if not isinstance(groups, list) or not isinstance(results, list):
        raise ValueError("Yedek dosyasının yapısı geçersiz")
    lesson_map = {}
    imported = skipped = 0
    self.conn.execute("BEGIN")
    try:
        for group in groups:
            key = str(group.get("key", "")).strip()
            name = self._validate_group_name(str(group.get("name", "")))
            is_custom = bool(group.get("is_custom", True))
            default_id = group.get("default_source_id")
            source_id = None
            if not is_custom and isinstance(default_id, int):
                if self.conn.execute("SELECT 1 FROM sources WHERE id = ?", (default_id,)).fetchone():
                    source_id = int(default_id)
            if source_id is None and key:
                found = self.conn.execute("SELECT id FROM sources WHERE custom_key = ?", (key,)).fetchone()
                if found:
                    source_id = int(found[0])
            if source_id is None:
                source_key = key or uuid.uuid4().hex
                relative_path = "" if not is_custom else _custom_relative_path(0, source_key)
                source_id = int(self.conn.execute(
                    """INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key)
                       VALUES (?, ?, ?, 0, ?)""",
                    (name, relative_path, int(is_custom), source_key),
                ).lastrowid)
            self.conn.execute(
                "UPDATE sources SET display_name = ?, is_deleted = 0, is_custom = ? WHERE id = ?",
                (name, int(is_custom), source_id),
            )
            for order, item in enumerate(group.get("lessons", [])):
                text = self._validate_text(str(item.get("text", "")))
                default_lesson_id = item.get("default_lesson_id")
                lesson_key = str(item.get("key", "")).strip() or uuid.uuid4().hex
                lesson_id = None
                if not is_custom and isinstance(default_lesson_id, int):
                    if self.conn.execute("SELECT 1 FROM lessons WHERE id = ?", (default_lesson_id,)).fetchone():
                        lesson_id = int(default_lesson_id)
                if lesson_id is None:
                    found = self.conn.execute("SELECT id FROM lessons WHERE custom_key = ?", (lesson_key,)).fetchone()
                    if found:
                        lesson_id = int(found[0])
                if lesson_id is not None:
                    self.conn.execute(
                        """UPDATE lessons SET source_id = ?, text = ?, custom_order = ?,
                           is_deleted = 0, is_custom = ? WHERE id = ?""",
                        (source_id, text, order, int(is_custom), lesson_id),
                    )
                else:
                    lesson_id = int(self.conn.execute(
                        """INSERT INTO lessons(
                               source_id, legacy_metin_id, title, text,
                               is_custom, is_deleted, custom_order, custom_key
                           ) VALUES (?, 0, 'Ders', ?, ?, 0, ?, ?)""",
                        (source_id, text, int(is_custom), order, lesson_key),
                    ).lastrowid)
                lesson_map[lesson_key] = lesson_id
        for result in results:
            try:
                completed = str(result.get("completed_at", ""))
                datetime.strptime(completed, "%Y-%m-%d %H:%M:%S")
                source_name = str(result.get("source_name", result.get("source_name_snapshot", "")))
                lesson_title = str(result.get("lesson_title", result.get("lesson_title_snapshot", "")))
                lesson_id = lesson_map.get(str(result.get("lesson_key", ""))) if result.get("lesson_key") else None
                if lesson_id is None and isinstance(result.get("lesson_id"), int):
                    found = self.conn.execute(
                        "SELECT id FROM lessons WHERE id = ? AND is_deleted = 0",
                        (int(result["lesson_id"]),),
                    ).fetchone()
                    lesson_id = int(found[0]) if found else None
                if lesson_id is None:
                    row = self.conn.execute(
                        """SELECT l.id FROM lessons l JOIN sources s ON s.id = l.source_id
                           WHERE l.is_deleted = 0 AND s.is_deleted = 0
                             AND s.display_name = ? AND l.title = ? LIMIT 1""",
                        (source_name, lesson_title),
                    ).fetchone()
                    lesson_id = int(row[0]) if row else None
                if lesson_id is None:
                    skipped += 1
                    continue
                values = (
                    lesson_id, float(result.get("duration_seconds", 0)),
                    int(result.get("correct_characters", 0)), int(result.get("wrong_characters", 0)),
                    float(result.get("words_per_minute", 0)), int(result.get("correct_words", 0)),
                    int(result.get("wrong_words", 0)), float(result.get("words_per_minute", 0)),
                    float(result.get("characters_per_minute", 0)), completed, source_name, lesson_title,
                    int(result.get("target_word_count", 0)), int(result.get("typed_word_count", 0)),
                    int(result.get("total_characters", 0)), int(result.get("correct_characters", 0)),
                    int(result.get("wrong_characters", 0)), float(result.get("accuracy_percent", 0)),
                )
                self.conn.execute(
                    """INSERT INTO practice_results(
                           lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                           correct_words, wrong_words, words_per_minute, characters_per_minute,
                           completed_at, source_name_snapshot, lesson_title_snapshot,
                           target_word_count, typed_word_count, total_characters,
                           correct_characters, wrong_characters, accuracy_percent
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    values,
                )
                imported += 1
            except (TypeError, ValueError):
                skipped += 1
        self.conn.commit()
        return imported, skipped
    except Exception:
        self.conn.rollback()
        raise


def _patch():
    Database.__init__ = _init
    Database.sources = _sources
    Database.lessons = _lessons
    Database._custom_lesson_position = _custom_lesson_position
    Database.managed_groups = _managed_groups
    Database.managed_lessons = _managed_lessons
    Database.rename_group = _rename_group
    Database.delete_group = _delete_group
    Database.create_custom_group = _create_custom_group
    Database.create_lesson = _create_lesson
    Database.update_lesson = _update_lesson
    Database.delete_lesson = _delete_lesson
    Database.move_lesson = _move_lesson
    Database.reset_all_content = _reset_all_content
    Database.restore_defaults = _restore_defaults
    Database.export_data = _export_data
    Database.import_data = _import_data


_patch()
