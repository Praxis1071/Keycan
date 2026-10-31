"""Read-only bridge between the packaged lesson catalog and SQLite user state.

The catalog supplies cleaned built-in names/text. SQLite remains authoritative for
user edits, deletions, ordering, custom content, and practice history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from keycan.services.lesson_catalog import (
    LessonCatalog,
    load_lesson_catalog,
)
from keycan.utils.text import natural_sort_key

if TYPE_CHECKING:
    from keycan.data.database import Database


@dataclass(frozen=True, slots=True)
class CatalogCoverage:
    missing_group_ids: tuple[int, ...]
    missing_lesson_ids: tuple[int, ...]
    extra_group_ids: tuple[int, ...]
    extra_lesson_ids: tuple[int, ...]

    @property
    def complete(self) -> bool:
        return not (
            self.missing_group_ids
            or self.missing_lesson_ids
            or self.extra_group_ids
            or self.extra_lesson_ids
        )


class LessonService:
    """Resolve built-in lesson content without changing the database."""

    def __init__(
        self,
        database: Database,
        catalog: LessonCatalog | None = None,
    ) -> None:
        self.database = database
        self.catalog = catalog or load_lesson_catalog()
        self._groups = {group.id: group for group in self.catalog.groups}
        self._lessons = {
            lesson.id: lesson
            for group in self.catalog.groups
            for lesson in group.lessons
        }

    @staticmethod
    def _normalized_text(value: str) -> str:
        """Remove legacy numbers/punctuation while preserving every letter and its order."""
        return " ".join(
            "".join(
                character if character.isalpha() or character.isspace() else " "
                for character in value
            ).split()
        )

    def _resolved_group_name(self, group_id: int, current_name: str, is_custom: bool) -> str:
        group = self._groups.get(group_id)
        if group is None or is_custom:
            return current_name
        # Only replace the known bundled legacy label. A different name is a
        # user rename and must remain untouched.
        if current_name == group.legacy_name:
            return group.name
        return current_name

    def _resolved_lesson_text(
        self,
        lesson_id: int,
        current_text: str,
        is_custom: bool = False,
    ) -> str:
        lesson = self._lessons.get(lesson_id)
        if lesson is None or is_custom:
            return current_text
        # A match after removing legacy punctuation/numbers means this is the
        # original lesson, not a user edit. Use the curated JSON text.
        if self._normalized_text(current_text) == self._normalized_text(lesson.text):
            return lesson.text
        return current_text

    def sources(self) -> list[tuple[int, str]]:
        visible = self.database.sources()
        managed = {
            int(group_id): (str(name), bool(is_custom))
            for group_id, name, _key, is_custom in self.database.managed_groups()
        }
        resolved: list[tuple[int, str]] = []
        for group_id, _display_name in visible:
            current = managed.get(int(group_id))
            if current is None:
                continue
            current_name, is_custom = current
            name = self._resolved_group_name(int(group_id), current_name, is_custom)
            resolved.append((int(group_id), name))
        resolved.sort(key=lambda row: natural_sort_key(row[1]))
        return [
            (group_id, self.database._display_source_name(name, index))
            for index, (group_id, name) in enumerate(resolved, 1)
        ]

    def lessons(self, group_id: int) -> list[tuple[int, str]]:
        return self.database.lessons(group_id)

    def lesson(self, lesson_id: int) -> tuple[int, str, str]:
        row_id, title, current_text = self.database.lesson(lesson_id)
        return (
            row_id,
            title,
            self._resolved_lesson_text(row_id, current_text),
        )

    def managed_groups(self) -> list[tuple[int, str, str, int]]:
        rows = self.database.managed_groups()
        resolved = [
            (
                int(group_id),
                self._resolved_group_name(int(group_id), str(name), bool(is_custom)),
                str(custom_key or ""),
                int(is_custom),
            )
            for group_id, name, custom_key, is_custom in rows
        ]
        resolved.sort(key=lambda row: natural_sort_key(row[1]))
        return resolved

    def managed_lessons(
        self,
        group_id: int,
    ) -> list[tuple[int, str, str, int, int]]:
        rows = self.database.managed_lessons(group_id)
        return [
            (
                int(lesson_id),
                self._resolved_lesson_text(
                    int(lesson_id), str(text), bool(is_custom)
                ),
                str(custom_key or ""),
                int(order),
                int(is_custom),
            )
            for lesson_id, text, custom_key, order, is_custom in rows
        ]

    def coverage(self) -> CatalogCoverage:
        """Report ID drift without creating, deleting, or rewriting any records."""
        db_group_ids = {
            int(row[0])
            for row in self.database.conn.execute(
                "SELECT id FROM sources WHERE is_custom = 0 AND EXISTS "
                "(SELECT 1 FROM lessons WHERE lessons.source_id = sources.id)"
            ).fetchall()
        }
        db_lesson_ids = {
            int(row[0])
            for row in self.database.conn.execute(
                "SELECT id FROM lessons WHERE is_custom = 0"
            ).fetchall()
        }
        catalog_group_ids = set(self._groups)
        catalog_lesson_ids = set(self._lessons)
        return CatalogCoverage(
            missing_group_ids=tuple(sorted(catalog_group_ids - db_group_ids)),
            missing_lesson_ids=tuple(sorted(catalog_lesson_ids - db_lesson_ids)),
            extra_group_ids=tuple(sorted(db_group_ids - catalog_group_ids)),
            extra_lesson_ids=tuple(sorted(db_lesson_ids - catalog_lesson_ids)),
        )
