"""Runtime compatibility and user-content management for Keycan."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key
from keycan.services.progression import session_xp, streaks

_ORIGINAL_INIT = Database.__init__


def _custom_relative_path(source_id: int, custom_key: str = "") -> str:
    key = custom_key.strip() or uuid.uuid4().hex
    return f"custom://{key}"


def _migrate_custom_relative_paths(self: Database) -> None:
    columns = {row[1] for row in self.conn.execute("PRAGMA table_info(sources)")}
    if "relative_path" not in columns:
        self.conn.execute("ALTER TABLE sources ADD COLUMN relative_path TEXT NOT NULL DEFAULT ''")
    rows = self.conn.execute(
        """SELECT id, display_name, custom_key, is_custom, relative_path
           FROM sources
           WHERE relative_path = '' OR relative_path IS NULL
           ORDER BY id"""
    ).fetchall()
    changed = False
    for source_id, _display_name, custom_key, is_custom, _relative_path in rows:
        key = str(custom_key or "").strip() or uuid.uuid4().hex
        path = _custom_relative_path(source_id, key) if is_custom else f"default://{source_id}"
        self.conn.execute(
            "UPDATE sources SET custom_key = ?, relative_path = ? WHERE id = ?",
            (key if is_custom else str(custom_key or ""), path, source_id),
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
               custom_order INTEGER NOT NULL DEFAULT 0,
               is_custom INTEGER NOT NULL DEFAULT 0,
               custom_key TEXT NOT NULL DEFAULT ''
           )"""
    )
    self.conn.execute(
        """CREATE TABLE IF NOT EXISTS content_restore_state (
               id INTEGER PRIMARY KEY CHECK (id = 1),
               snapshot_pending INTEGER NOT NULL DEFAULT 0
           )"""
    )
    self.conn.execute(
        "INSERT OR IGNORE INTO content_restore_state(id, snapshot_pending) VALUES (1, 0)"
    )
    columns = {
        row[1] for row in self.conn.execute(
            "PRAGMA table_info(default_content_lessons)"
        ).fetchall()
    }
    if "is_custom" not in columns:
        self.conn.execute(
            "ALTER TABLE default_content_lessons ADD COLUMN is_custom INTEGER NOT NULL DEFAULT 0"
        )
    if "custom_key" not in columns:
        self.conn.execute(
            "ALTER TABLE default_content_lessons ADD COLUMN custom_key TEXT NOT NULL DEFAULT ''"
        )
    if self.conn.execute("SELECT COUNT(*) FROM default_content_sources").fetchone()[0] == 0:
        source_rows = self.conn.execute(
            """SELECT id, display_name, relative_path, custom_key
               FROM sources WHERE is_custom = 0 AND is_deleted = 0 ORDER BY id"""
        ).fetchall()
        lesson_rows = self.conn.execute(
            """SELECT l.id, l.source_id, l.legacy_metin_id, l.title, l.text,
                      l.custom_order, l.is_custom, COALESCE(l.custom_key, '')
               FROM lessons AS l JOIN sources AS s ON s.id = l.source_id
               WHERE s.is_custom = 0 AND s.is_deleted = 0 AND l.is_deleted = 0
               ORDER BY l.source_id, l.custom_order, l.legacy_metin_id, l.id"""
        ).fetchall()
        for row in source_rows:
            self.conn.execute("INSERT INTO default_content_sources VALUES (?,?,?,?)", row)
        for row in lesson_rows:
            self.conn.execute(
                """INSERT INTO default_content_lessons(
                       lesson_id, source_id, legacy_metin_id, title, text,
                       custom_order, is_custom, custom_key
                   ) VALUES (?,?,?,?,?,?,?,?)""", row
            )
        self.conn.commit()


def _sync_default_snapshot(self: Database) -> None:
    """Mirror the currently active built-in workspace content for later restore."""
    source_rows = self.conn.execute(
        """SELECT id, display_name, relative_path, COALESCE(custom_key, '')
           FROM sources WHERE is_custom = 0 AND is_deleted = 0 ORDER BY id"""
    ).fetchall()
    lesson_rows = self.conn.execute(
        """SELECT l.id, l.source_id, l.legacy_metin_id, l.title, l.text,
                  l.custom_order, l.is_custom, COALESCE(l.custom_key, '')
           FROM lessons AS l JOIN sources AS s ON s.id = l.source_id
           WHERE s.is_custom = 0 AND s.is_deleted = 0 AND l.is_deleted = 0
           ORDER BY l.source_id, l.custom_order, l.legacy_metin_id, l.id"""
    ).fetchall()
    self.conn.execute("BEGIN")
    try:
        self.conn.execute("DELETE FROM default_content_lessons")
        self.conn.execute("DELETE FROM default_content_sources")
        self.conn.executemany(
            "INSERT INTO default_content_sources VALUES (?,?,?,?)", source_rows
        )
        self.conn.executemany(
            """INSERT INTO default_content_lessons(
                   lesson_id, source_id, legacy_metin_id, title, text,
                   custom_order, is_custom, custom_key
               ) VALUES (?,?,?,?,?,?,?,?)""", lesson_rows
        )
        self.conn.execute(
            "UPDATE content_restore_state SET snapshot_pending = 0 WHERE id = 1"
        )
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise


def _init(self: Database, path):
    _ORIGINAL_INIT(self, path)
    _ensure_default_snapshot(self)
    snapshot_pending = self.conn.execute(
        "SELECT snapshot_pending FROM content_restore_state WHERE id = 1"
    ).fetchone()[0]
    if not snapshot_pending:
        # Reconcile legacy snapshots against the actual active workspace.
        # A full reset explicitly marks its restore point as pending.
        _sync_default_snapshot(self)


def _sources(self: Database):
    rows = self.conn.execute(
        "SELECT id, display_name, is_custom FROM sources WHERE is_deleted = 0 ORDER BY display_name COLLATE NOCASE, id"
    ).fetchall()
    visible = []
    for source_id, name, is_custom in rows:
        has_lessons = self.conn.execute(
            "SELECT 1 FROM lessons WHERE source_id = ? AND is_deleted = 0 LIMIT 1", (source_id,)
        ).fetchone()
        if has_lessons or is_custom:
            visible.append((source_id, clean_source_name(name), bool(is_custom)))
    visible.sort(key=lambda row: natural_sort_key(row[1]))
    return [(source_id, self._display_source_name(name, index)) for index, (source_id, name, _is_custom) in enumerate(visible, 1)]


def _lessons(self: Database, source_id: int):
    rows = self.conn.execute(
        "SELECT id FROM lessons WHERE source_id = ? AND is_deleted = 0 ORDER BY custom_order, legacy_metin_id, id",
        (source_id,),
    ).fetchall()
    return [(lesson_id, f"Ders {index}") for index, (lesson_id,) in enumerate(rows, 1)]


def _custom_lesson_position(self: Database, lesson_id: int) -> int:
    row = self.conn.execute("SELECT source_id, custom_order FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    source_id, order = row
    return int(self.conn.execute(
        """SELECT COUNT(*) FROM lessons WHERE source_id = ? AND is_deleted = 0
           AND (custom_order < ? OR (custom_order = ? AND id <= ?))""",
        (source_id, order, order, lesson_id),
    ).fetchone()[0])


def _managed_groups(self: Database):
    return self.conn.execute(
        "SELECT id, display_name, custom_key, is_custom FROM sources WHERE is_deleted = 0 ORDER BY display_name COLLATE NOCASE, id"
    ).fetchall()


def _managed_lessons(self: Database, source_id: int):
    return self.conn.execute(
        """SELECT id, text, custom_key, custom_order, is_custom FROM lessons
           WHERE source_id = ? AND is_deleted = 0 ORDER BY custom_order, legacy_metin_id, id""",
        (source_id,),
    ).fetchall()


def _rename_group(self: Database, source_id: int, name: str) -> None:
    name = self._validate_group_name(name)
    row = self.conn.execute(
        "SELECT is_custom FROM sources WHERE id = ? AND is_deleted = 0", (source_id,)
    ).fetchone()
    if not row:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.execute("UPDATE sources SET display_name = ? WHERE id = ?", (name, source_id))
    self.conn.commit()
    if not row[0]:
        _sync_default_snapshot(self)


def _delete_group(self: Database, source_id: int) -> None:
    row = self.conn.execute(
        "SELECT is_custom FROM sources WHERE id = ? AND is_deleted = 0", (source_id,)
    ).fetchone()
    if not row:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.execute("UPDATE sources SET is_deleted = 1 WHERE id = ?", (source_id,))
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE source_id = ?", (source_id,))
    self.conn.commit()
    if not row[0]:
        _sync_default_snapshot(self)


def _create_custom_group(self: Database, name: str) -> int:
    name = self._validate_group_name(name)
    key = uuid.uuid4().hex
    cursor = self.conn.execute(
        """INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key)
           VALUES (?, ?, 1, 0, ?)""",
        (name, _custom_relative_path(0, key), key),
    )
    self.conn.commit()
    return int(cursor.lastrowid)


def _create_lesson(self: Database, source_id: int, text: str) -> int:
    text = self._validate_text(text)
    source = self.conn.execute(
        "SELECT is_custom FROM sources WHERE id = ? AND is_deleted = 0", (source_id,)
    ).fetchone()
    if not source:
        raise ValueError("Ders grubu bulunamadı")
    order = self.conn.execute(
        "SELECT COALESCE(MAX(custom_order), -1) + 1 FROM lessons WHERE source_id = ? AND is_deleted = 0", (source_id,)
    ).fetchone()[0]
    key = uuid.uuid4().hex
    lesson_id = int(self.conn.execute(
        """INSERT INTO lessons(source_id, legacy_metin_id, title, text, is_custom, is_deleted, custom_order, custom_key)
           VALUES (?, 0, 'Ders', ?, 1, 0, ?, ?)""",
        (source_id, text, order, key),
    ).lastrowid)
    self.conn.commit()
    if not source[0]:
        _sync_default_snapshot(self)
    return lesson_id


def _update_lesson(self: Database, lesson_id: int, text: str) -> None:
    text = self._validate_text(text)
    source = self.conn.execute(
        """SELECT s.is_custom FROM lessons AS l
           JOIN sources AS s ON s.id = l.source_id
           WHERE l.id = ? AND l.is_deleted = 0 AND s.is_deleted = 0""",
        (lesson_id,),
    ).fetchone()
    if not source:
        raise ValueError("Metin bulunamadı")
    self.conn.execute("UPDATE lessons SET text = ? WHERE id = ?", (text, lesson_id))
    self.conn.commit()
    if not source[0]:
        _sync_default_snapshot(self)


def _delete_lesson(self: Database, lesson_id: int) -> None:
    row = self.conn.execute(
        """SELECT l.source_id, s.is_custom FROM lessons AS l
           JOIN sources AS s ON s.id = l.source_id
           WHERE l.id = ? AND l.is_deleted = 0 AND s.is_deleted = 0""",
        (lesson_id,),
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE id = ?", (lesson_id,))
    self.conn.commit()
    _normalize_order(self, int(row[0]))
    if not row[1]:
        _sync_default_snapshot(self)


def _move_lesson(self: Database, lesson_id: int, direction: int) -> None:
    if direction not in (-1, 1):
        raise ValueError("Geçersiz sıralama yönü")
    row = self.conn.execute(
        """SELECT l.source_id, s.is_custom FROM lessons AS l
           JOIN sources AS s ON s.id = l.source_id
           WHERE l.id = ? AND l.is_deleted = 0 AND s.is_deleted = 0""",
        (lesson_id,),
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    source_id = int(row[0])
    ids = [r[0] for r in self.conn.execute(
        "SELECT id FROM lessons WHERE source_id = ? AND is_deleted = 0 ORDER BY custom_order, legacy_metin_id, id", (source_id,)
    ).fetchall()]
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
    if not row[1]:
        _sync_default_snapshot(self)


def _normalize_order(self: Database, source_id: int) -> None:
    rows = self.conn.execute(
        "SELECT id FROM lessons WHERE source_id = ? AND is_deleted = 0 ORDER BY custom_order, legacy_metin_id, id", (source_id,)
    ).fetchall()
    for order, (lesson_id,) in enumerate(rows):
        self.conn.execute("UPDATE lessons SET custom_order = ? WHERE id = ?", (order, lesson_id))
    self.conn.commit()


def _progression_summary(self: Database):
    rows = self.conn.execute(
        """SELECT completed_at, duration_seconds, typed_word_count,
                  words_per_minute, accuracy_percent
           FROM practice_results
           WHERE completed_at != ''
           ORDER BY completed_at ASC, id ASC"""
    ).fetchall()
    xp = 0
    max_wpm = 0.0
    max_accuracy = 0.0
    max_duration = 0.0
    timestamps = []
    for completed_at, duration, words, wpm, accuracy in rows:
        duration = float(duration)
        words = int(words)
        wpm = float(wpm)
        accuracy = float(accuracy)
        xp += session_xp(
            duration_seconds=duration,
            typed_word_count=words,
            words_per_minute=wpm,
            accuracy_percent=accuracy,
        )
        max_wpm = max(max_wpm, wpm)
        max_accuracy = max(max_accuracy, accuracy)
        max_duration = max(max_duration, duration)
        timestamps.append(self._parse_completed_at(str(completed_at)).strftime("%Y-%m-%d %H:%M:%S"))
    current_streak, best_streak = streaks(timestamps)
    totals = self.conn.execute(
        """SELECT
               COALESCE(SUM(duration_seconds), 0),
               COALESCE(SUM(typed_word_count), 0),
               COALESCE(SUM(total_characters), 0),
               COALESCE(AVG(words_per_minute), 0),
               COALESCE(AVG(accuracy_percent), 0),
               COUNT(DISTINCT lesson_id)
           FROM practice_results
           WHERE completed_at != ''"""
    ).fetchone()
    total_duration, total_words, total_characters, average_wpm, average_accuracy, completed_lessons = totals
    recent_rows = self.conn.execute(
        """SELECT completed_at, words_per_minute, accuracy_percent, duration_seconds
           FROM practice_results
           WHERE completed_at != ''
           ORDER BY completed_at DESC, id DESC
           LIMIT 5"""
    ).fetchall()
    recent_sessions = [
        {
            "completed_at": str(completed_at),
            "wpm": float(wpm),
            "accuracy": float(accuracy),
            "duration_seconds": float(duration),
        }
        for completed_at, wpm, accuracy, duration in recent_rows
    ]
    return {
        "xp": xp,
        "sessions": len(rows),
        "max_wpm": max_wpm,
        "max_accuracy": max_accuracy,
        "max_duration_seconds": max_duration,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_duration_seconds": float(total_duration),
        "total_words": int(total_words),
        "total_characters": int(total_characters),
        "average_wpm": float(average_wpm),
        "average_accuracy": float(average_accuracy),
        "completed_lessons": int(completed_lessons),
        "recent_sessions": recent_sessions,
    }


def _reset_all_content(self: Database):
    _ensure_default_snapshot(self)
    pending = self.conn.execute(
        "SELECT snapshot_pending FROM content_restore_state WHERE id = 1"
    ).fetchone()[0]
    # Capture the latest active workspace before hiding everything, unless a
    # full reset already has a valid restore point waiting to be used.
    if not pending:
        _sync_default_snapshot(self)
    groups = int(self.conn.execute("SELECT COUNT(*) FROM sources WHERE is_deleted = 0").fetchone()[0])
    lessons = int(self.conn.execute("SELECT COUNT(*) FROM lessons WHERE is_deleted = 0").fetchone()[0])
    self.conn.execute("UPDATE lessons SET is_deleted = 1 WHERE is_deleted = 0")
    self.conn.execute("UPDATE sources SET is_deleted = 1 WHERE is_deleted = 0")
    self.conn.execute(
        "UPDATE content_restore_state SET snapshot_pending = 1 WHERE id = 1"
    )
    self.conn.commit()
    return groups, lessons


def _restore_defaults(self: Database):
    _ensure_default_snapshot(self)
    source_rows = self.conn.execute("SELECT source_id, display_name, relative_path, custom_key FROM default_content_sources ORDER BY source_id").fetchall()
    lesson_rows = self.conn.execute(
        """SELECT lesson_id, source_id, legacy_metin_id, title, text,
                  custom_order, is_custom, custom_key
           FROM default_content_lessons
           ORDER BY source_id, custom_order, lesson_id"""
    ).fetchall()
    self.conn.execute("BEGIN")
    try:
        for source_id, name, path, key in source_rows:
            # A restore resets built-in lesson content, not the user's chosen
            # display label. Only a physically missing source receives the
            # original snapshot name.
            self.conn.execute(
                """INSERT OR IGNORE INTO sources(
                       id, display_name, relative_path, is_custom, is_deleted, custom_key
                   ) VALUES (?, ?, ?, 0, 0, ?)""",
                (source_id, name, path, key),
            )
            self.conn.execute(
                """UPDATE sources
                   SET relative_path = ?, custom_key = ?, is_custom = 0, is_deleted = 0
                   WHERE id = ?""",
                (path, key, source_id),
            )
        ids = [row[0] for row in source_rows]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            self.conn.execute(f"UPDATE lessons SET is_deleted = 1 WHERE source_id IN ({placeholders})", tuple(ids))
        for lesson_id, source_id, legacy_id, title, text, order, is_custom, custom_key in lesson_rows:
            self.conn.execute(
                """UPDATE lessons SET source_id = ?, legacy_metin_id = ?, title = ?, text = ?,
                   is_custom = ?, is_deleted = 0, custom_order = ?, custom_key = ? WHERE id = ?""",
                (source_id, legacy_id, title, text, is_custom, order, custom_key, lesson_id),
            )
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise
    _sync_default_snapshot(self)
    return len(source_rows), len(lesson_rows)


def _default_source_identity(self: Database, source_id: int) -> str:
    source = self.conn.execute(
        "SELECT display_name FROM default_content_sources WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    if not source:
        return ""
    lessons = self.conn.execute(
        """SELECT legacy_metin_id, title, text
           FROM default_content_lessons
           WHERE source_id = ?
           ORDER BY custom_order, legacy_metin_id, title""",
        (source_id,),
    ).fetchall()
    payload = json.dumps(
        {"name": source[0], "lessons": lessons},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "default-source:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_lesson_identity(self: Database, lesson_id: int) -> str:
    row = self.conn.execute(
        """SELECT source_id, legacy_metin_id, title, text
           FROM default_content_lessons WHERE lesson_id = ?""",
        (lesson_id,),
    ).fetchone()
    if not row:
        return ""
    source_id, legacy_id, title, text = row
    source_identity = _default_source_identity(self, int(source_id))
    if not source_identity:
        return ""
    payload = json.dumps(
        [source_identity, int(legacy_id), str(title), str(text)],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "default-lesson:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _export_data(self: Database) -> str:
    # Backups include soft-deleted content as well. A deleted lesson may still
    # own historical sessions, so omitting it would make those sessions
    # impossible to map when restoring the backup elsewhere.
    groups = []
    source_rows = self.conn.execute(
        """SELECT id, display_name, custom_key, is_custom, is_deleted
           FROM sources ORDER BY id"""
    ).fetchall()
    for source_id, name, key, is_custom, source_deleted in source_rows:
        group_key = key or f"default:{source_id}"
        source_identity = "" if is_custom else _default_source_identity(self, source_id)
        lessons = []
        lesson_rows = self.conn.execute(
            """SELECT id, text, custom_key, custom_order, is_custom, is_deleted,
                      title, legacy_metin_id
               FROM lessons WHERE source_id = ?
               ORDER BY custom_order, legacy_metin_id, id""",
            (source_id,),
        ).fetchall()
        for lesson_id, text, lesson_key, order, lesson_custom, lesson_deleted, title, legacy_id in lesson_rows:
            lesson_identity = "" if lesson_custom else _default_lesson_identity(self, lesson_id)
            lessons.append({
                "key": lesson_key or f"default:{lesson_id}",
                "identity": lesson_identity or None,
                "text": text,
                "title": title,
                "legacy_metin_id": legacy_id,
                "order": order,
                "is_custom": bool(lesson_custom),
                "is_deleted": bool(lesson_deleted),
                "default_lesson_id": None if lesson_custom else lesson_id,
            })
        groups.append({
            "key": group_key,
            "identity": source_identity or None,
            "name": name,
            "lessons": lessons,
            "is_custom": bool(is_custom),
            "is_deleted": bool(source_deleted),
            "default_source_id": None if is_custom else source_id,
        })

    rows = self.conn.execute(
        """SELECT r.completed_at, r.duration_seconds, r.correct_words, r.wrong_words,
                  r.words_per_minute, r.characters_per_minute, r.target_word_count,
                  r.typed_word_count, r.total_characters, r.correct_characters,
                  r.wrong_characters, r.accuracy_percent, r.wrong_letter_counts,
                  r.source_name_snapshot, r.lesson_title_snapshot, s.custom_key,
                  l.custom_key, l.id, s.id, r.session_uuid
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
        "wrong_characters", "accuracy_percent", "wrong_letter_counts",
        "source_name", "lesson_title", "source_key", "lesson_key",
        "lesson_id", "source_id", "session_uuid",
    )
    practice_results = []
    for row in rows:
        item = dict(zip(fields, row))
        item["source_key"] = item["source_key"] or f"default:{item['source_id']}"
        item["lesson_key"] = item["lesson_key"] or f"default:{item['lesson_id']}"
        source_id = item["source_id"]
        lesson_id = item["lesson_id"]
        item["source_identity"] = (
            _default_source_identity(self, int(source_id))
            if source_id is not None else ""
        ) or None
        item["lesson_identity"] = (
            _default_lesson_identity(self, int(lesson_id))
            if lesson_id is not None else ""
        ) or None
        practice_results.append(item)

    return json.dumps({
        "format": "keycan-backup",
        "version": 3,
        "exported_at": datetime.now().astimezone().isoformat(),
        "groups": groups,
        "practice_results": practice_results,
    }, ensure_ascii=False, indent=2)


def _import_data(self: Database, raw: str):
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Yedek dosyasının kök yapısı geçersiz")
    if payload.get("format") != "keycan-backup" or payload.get("version") not in (1, 2, 3):
        raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
    groups = payload.get("groups", payload.get("custom_groups", []))
    results = payload.get("practice_results", [])
    if not isinstance(groups, list) or not isinstance(results, list):
        raise ValueError("Yedek dosyasının yapısı geçersiz")
    if any(not isinstance(group, dict) or not isinstance(group.get("lessons", []), list)
           or any(not isinstance(item, dict) for item in group.get("lessons", []))
           for group in groups):
        raise ValueError("Yedek dosyasındaki ders grupları veya metinler geçersiz")
    if any(not isinstance(item, dict) for item in results):
        raise ValueError("Yedek dosyasındaki çalışma kayıtları geçersiz")
    lesson_map = {}
    source_map = {}
    source_id_map = {}
    source_deleted = {}
    lesson_deleted = {}
    imported = skipped = 0
    self.conn.execute("BEGIN")
    try:
        for group in groups:
            key = str(group.get("key", "")).strip()
            name = self._validate_group_name(str(group.get("name", "")))
            is_custom = bool(group.get("is_custom", True))
            default_id = group.get("default_source_id")
            source_id = None
            source_identity = str(group.get("identity", "")).strip()
            if not is_custom and source_identity:
                for (candidate_id,) in self.conn.execute(
                    "SELECT id FROM sources WHERE is_custom = 0"
                ).fetchall():
                    if _default_source_identity(self, int(candidate_id)) == source_identity:
                        source_id = int(candidate_id)
                        break
            elif not is_custom and isinstance(default_id, int):
                # Legacy backups lack content identities. Reuse a numeric ID
                # only when its source name also agrees; never trust IDs alone.
                found = self.conn.execute(
                    """SELECT id FROM sources
                       WHERE id = ? AND is_custom = 0 AND display_name = ?""",
                    (default_id, name),
                ).fetchone()
                if found:
                    source_id = int(found[0])
            if source_id is None and source_identity:
                found = self.conn.execute(
                    "SELECT id FROM sources WHERE custom_key = ? AND is_custom = 0",
                    (source_identity,),
                ).fetchone()
                if found:
                    source_id = int(found[0])
            if source_id is None and key:
                found = self.conn.execute(
                    "SELECT id FROM sources WHERE custom_key = ? AND is_custom = ?",
                    (key, int(is_custom)),
                ).fetchone()
                if found:
                    source_id = int(found[0])
            if source_id is None:
                source_key = (source_identity or key) if not is_custom else (key or uuid.uuid4().hex)
                relative_path = _custom_relative_path(0, source_key) if is_custom else f"default://{source_key}"
                source_id = int(self.conn.execute(
                    """INSERT INTO sources(display_name, relative_path, is_custom, is_deleted, custom_key)
                       VALUES (?, ?, ?, 0, ?)""",
                    (name, relative_path, int(is_custom), source_key),
                ).lastrowid)
            self.conn.execute("UPDATE sources SET display_name = ?, is_deleted = 0, is_custom = ? WHERE id = ?", (name, int(is_custom), source_id))
            if key:
                source_map[key] = source_id
            if source_identity:
                source_map[source_identity] = source_id
            if not is_custom and isinstance(default_id, int):
                source_id_map[default_id] = source_id
            source_deleted[source_id] = bool(group.get("is_deleted", False))
            imported += 1
            for order, item in enumerate(group.get("lessons", [])):
                text = self._validate_text(str(item.get("text", "")))
                lesson_is_custom = bool(
                    item.get(
                        "is_custom",
                        is_custom or (
                            "default_lesson_id" in item
                            and item.get("default_lesson_id") is None
                        ),
                    )
                )
                default_lesson_id = item.get("default_lesson_id")
                lesson_key = str(item.get("key", "")).strip() or uuid.uuid4().hex
                lesson_id = None
                lesson_identity = str(item.get("identity", "")).strip()
                if not lesson_is_custom and lesson_identity:
                    for (candidate_id,) in self.conn.execute(
                        """SELECT id FROM lessons
                           WHERE source_id = ? AND is_custom = 0""",
                        (source_id,),
                    ).fetchall():
                        if _default_lesson_identity(self, int(candidate_id)) == lesson_identity:
                            lesson_id = int(candidate_id)
                            break
                elif not lesson_is_custom and isinstance(default_lesson_id, int):
                    found = self.conn.execute(
                        """SELECT id FROM lessons
                           WHERE id = ? AND source_id = ? AND is_custom = 0
                             AND text = ?""",
                        (default_lesson_id, source_id, text),
                    ).fetchone()
                    if found:
                        lesson_id = int(found[0])
                stored_lesson_key = lesson_identity or lesson_key
                if lesson_id is None:
                    found = self.conn.execute(
                        "SELECT id FROM lessons WHERE custom_key = ? AND source_id = ? AND is_custom = ?",
                        (stored_lesson_key, source_id, int(lesson_is_custom)),
                    ).fetchone()
                    if found:
                        lesson_id = int(found[0])
                if lesson_id is not None:
                    self.conn.execute("UPDATE lessons SET source_id = ?, text = ?, custom_order = ?, is_deleted = 0, is_custom = ? WHERE id = ?", (source_id, text, order, int(lesson_is_custom), lesson_id))
                else:
                    lesson_id = int(self.conn.execute(
                        """INSERT INTO lessons(source_id, legacy_metin_id, title, text, is_custom, is_deleted, custom_order, custom_key)
                           VALUES (?, 0, 'Ders', ?, ?, 0, ?, ?)""",
                        (source_id, text, int(lesson_is_custom), order, stored_lesson_key),
                    ).lastrowid)
                lesson_map[lesson_key] = lesson_id
                if lesson_identity:
                    lesson_map[lesson_identity] = lesson_id
                lesson_deleted[lesson_id] = bool(item.get("is_deleted", False))
                imported += 1
        for result in results:
            try:
                completed = str(result.get("completed_at", ""))
                try:
                    datetime.fromisoformat(completed.replace("Z", "+00:00"))
                except ValueError:
                    datetime.strptime(completed, "%Y-%m-%d %H:%M:%S")
                source_name = str(result.get("source_name", result.get("source_name_snapshot", "")))
                lesson_title = str(result.get("lesson_title", result.get("lesson_title_snapshot", "")))
                lesson_key = str(result.get("lesson_key", "")).strip()
                lesson_identity = str(result.get("lesson_identity", "")).strip()
                source_key = str(result.get("source_key", "")).strip()
                source_identity = str(result.get("source_identity", "")).strip()
                lesson_id = lesson_map.get(lesson_identity) if lesson_identity else None
                if lesson_id is None and lesson_key:
                    # Prefer the exported key as a compatibility fallback if
                    # a backup has been transformed by an older/custom tool.
                    lesson_id = lesson_map.get(lesson_key)
                mapped_source_id = (
                    source_map.get(source_key)
                    or source_map.get(source_identity)
                    or source_id_map.get(result.get("source_id"))
                )
                if lesson_id is None and isinstance(result.get("lesson_id"), int):
                    # Numeric lesson IDs are only meaningful inside a source
                    # that has already been resolved safely.
                    if mapped_source_id is not None:
                        found = self.conn.execute(
                            "SELECT id FROM lessons WHERE id = ? AND source_id = ? AND is_deleted = 0",
                            (int(result["lesson_id"]), mapped_source_id),
                        ).fetchone()
                        lesson_id = int(found[0]) if found else None
                if lesson_id is None:
                    query = """SELECT l.id FROM lessons l JOIN sources s ON s.id = l.source_id
                               WHERE l.is_deleted = 0 AND s.is_deleted = 0
                                 AND s.display_name = ? AND l.title = ?"""
                    params = [source_name, lesson_title]
                    if mapped_source_id is not None:
                        query += " AND s.id = ?"
                        params.append(mapped_source_id)
                    rows_found = self.conn.execute(query, tuple(params)).fetchall()
                    # Ambiguous legacy matches must never attach history to
                    # an arbitrary same-named lesson.
                    if len(rows_found) == 1:
                        lesson_id = int(rows_found[0][0])
                if lesson_id is None:
                    skipped += 1
                    continue
                duration_seconds = float(result.get("duration_seconds", 0))
                correct_words = int(result.get("correct_words", 0))
                wrong_words = int(result.get("wrong_words", 0))
                words_per_minute = float(result.get("words_per_minute", 0))
                characters_per_minute = float(result.get("characters_per_minute", 0))
                target_word_count = int(result.get("target_word_count", 0))
                typed_word_count = int(result.get("typed_word_count", 0))
                total_characters = int(result.get("total_characters", 0))
                correct_characters = int(result.get("correct_characters", 0))
                wrong_characters = int(result.get("wrong_characters", 0))
                accuracy_percent = float(result.get("accuracy_percent", 0))
                numeric_metrics = (
                    duration_seconds, correct_words, wrong_words, words_per_minute,
                    characters_per_minute, target_word_count, typed_word_count,
                    total_characters, correct_characters, wrong_characters,
                    accuracy_percent,
                )
                if any(not math.isfinite(value) or value < 0 for value in numeric_metrics):
                    raise ValueError("Yedekteki çalışma ölçümleri geçersiz")
                if correct_words + wrong_words != typed_word_count:
                    raise ValueError("Yedekteki kelime ölçümleri tutarsız")
                if total_characters != correct_characters + wrong_characters:
                    raise ValueError("Yedekteki karakter ölçümleri tutarsız")
                if accuracy_percent > 100:
                    raise ValueError("Yedekteki doğruluk yüzdesi geçersiz")
                normalized_wrong_letters = self._normalize_wrong_letter_counts(
                    result.get("wrong_letter_counts", {})
                )
                session_uuid = str(result.get("session_uuid", "")).strip()
                has_session_uuid = bool(session_uuid)
                if has_session_uuid:
                    existing_session = self.conn.execute(
                        "SELECT 1 FROM practice_results WHERE session_uuid = ?",
                        (session_uuid,),
                    ).fetchone()
                    if existing_session:
                        skipped += 1
                        continue
                else:
                    session_uuid = uuid.uuid4().hex
                candidates = self.conn.execute(
                    """SELECT duration_seconds, correct_words, wrong_words,
                              words_per_minute, characters_per_minute,
                              target_word_count, typed_word_count, total_characters,
                              correct_characters, wrong_characters, accuracy_percent,
                              wrong_letter_counts
                       FROM practice_results
                       WHERE lesson_id = ? AND completed_at = ?""",
                    (lesson_id, completed),
                ).fetchall()
                duplicate = False
                # V1/V2 backups have no stable session identifier. Retain the
                # legacy metric-based fallback only for those older records.
                legacy_candidates = candidates if not has_session_uuid else ()
                for existing in legacy_candidates:
                    try:
                        existing_wrong_letters = self._normalize_wrong_letter_counts(existing[11])
                    except ValueError:
                        continue
                    if (
                        float(existing[0]) == duration_seconds
                        and int(existing[1]) == correct_words
                        and int(existing[2]) == wrong_words
                        and float(existing[3]) == words_per_minute
                        and float(existing[4]) == characters_per_minute
                        and int(existing[5]) == target_word_count
                        and int(existing[6]) == typed_word_count
                        and int(existing[7]) == total_characters
                        and int(existing[8]) == correct_characters
                        and int(existing[9]) == wrong_characters
                        and float(existing[10]) == accuracy_percent
                        and existing_wrong_letters == normalized_wrong_letters
                    ):
                        duplicate = True
                        break
                if duplicate:
                    skipped += 1
                    continue
                values = (
                    lesson_id, duration_seconds, correct_characters,
                    wrong_characters, words_per_minute,
                    correct_words, wrong_words,
                    words_per_minute, characters_per_minute,
                    completed, source_name, lesson_title, target_word_count,
                    typed_word_count, total_characters,
                    correct_characters, wrong_characters,
                    accuracy_percent,
                    json.dumps(normalized_wrong_letters, ensure_ascii=False, sort_keys=True),
                    session_uuid,
                )
                self.conn.execute(
                    """INSERT INTO practice_results(lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                       correct_words, wrong_words, words_per_minute, characters_per_minute, completed_at,
                       source_name_snapshot, lesson_title_snapshot, target_word_count, typed_word_count,
                       total_characters, correct_characters, wrong_characters, accuracy_percent, wrong_letter_counts,
                       session_uuid)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    values,
                )
                imported += 1
            except (TypeError, ValueError, OverflowError):
                skipped += 1
        # Restore deletion state only after sessions have been mapped and
        # inserted, so history belonging to deleted lessons is not discarded.
        for source_id, deleted in source_deleted.items():
            self.conn.execute(
                "UPDATE sources SET is_deleted = ? WHERE id = ?",
                (int(deleted), source_id),
            )
        for lesson_id, deleted in lesson_deleted.items():
            self.conn.execute(
                "UPDATE lessons SET is_deleted = ? WHERE id = ?",
                (int(deleted), lesson_id),
            )
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
    Database.progression_summary = _progression_summary
    Database.reset_all_content = _reset_all_content
    Database.restore_defaults = _restore_defaults
    Database.export_data = _export_data
    Database.import_data = _import_data


_patch()
