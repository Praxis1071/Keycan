"""Final runtime compatibility layer for the user-content UI."""

from __future__ import annotations

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key


def sources(self: Database) -> list[tuple[int, str]]:
    rows = self.conn.execute("SELECT id, display_name, is_custom FROM sources WHERE is_deleted = 0").fetchall()
    visible = []
    for source_id, name, is_custom in rows:
        has_lessons = self.conn.execute("SELECT 1 FROM lessons WHERE source_id = ? AND is_deleted = 0 LIMIT 1", (source_id,)).fetchone()
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


def lessons(self: Database, source_id: int) -> list[tuple[int, str]]:
    custom = self.conn.execute("SELECT is_custom FROM sources WHERE id = ? AND is_deleted = 0", (source_id,)).fetchone()
    if custom and custom[0]:
        rows = self.conn.execute("SELECT id FROM lessons WHERE source_id = ? AND is_custom = 1 AND is_deleted = 0 ORDER BY custom_order, id", (source_id,)).fetchall()
        return [(lesson_id, str(index)) for index, (lesson_id,) in enumerate(rows, 1)]
    rows = self.conn.execute("SELECT id FROM lessons WHERE source_id = ? AND is_deleted = 0 ORDER BY legacy_metin_id, id", (source_id,)).fetchall()
    return [(lesson_id, f"Ders {index}") for index, (lesson_id,) in enumerate(rows, 1)]


Database.sources = sources
Database.lessons = lessons
