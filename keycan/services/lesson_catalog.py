from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class LessonCatalogError(ValueError):
    """Raised when a packaged lesson catalog is missing or invalid."""


@dataclass(frozen=True, slots=True)
class LessonEntry:
    id: int
    legacy_metin_id: int
    legacy_title: str
    order: int
    text: str


@dataclass(frozen=True, slots=True)
class LessonGroup:
    id: int
    name: str
    order: int
    lessons: tuple[LessonEntry, ...]


@dataclass(frozen=True, slots=True)
class LessonCatalog:
    language: str
    groups: tuple[LessonGroup, ...]


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LessonCatalogError(f"Geçersiz ders kataloğu alanı: {field}")
    return value


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LessonCatalogError(f"Geçersiz ders kataloğu alanı: {field}")
    return value


def _letters_and_spaces(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or any(
        not (character.isalpha() or character == " ") for character in value
    ):
        raise LessonCatalogError(f"{field} yalnızca harf ve boşluk içerebilir")
    if value != " ".join(value.split()):
        raise LessonCatalogError(f"{field} boşluk biçimi geçersiz")
    return value


def load_lesson_catalog(path: Path | None = None) -> LessonCatalog:
    """Load and validate the versioned packaged lesson catalog."""
    catalog_path = path or (
        Path(__file__).resolve().parents[1]
        / "resources"
        / "lessons"
        / "tr"
        / "catalog.json"
    )
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LessonCatalogError(f"Ders kataloğu okunamadı: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise LessonCatalogError("Ders kataloğu JSON biçimi geçersiz") from exc

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise LessonCatalogError("Desteklenmeyen ders kataloğu sürümü")
    if payload.get("language") != "tr":
        raise LessonCatalogError("Ders kataloğunun dili geçersiz")
    raw_groups = payload.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise LessonCatalogError("Ders kataloğunda grup bulunamadı")

    groups: list[LessonGroup] = []
    group_ids: set[int] = set()
    group_names: set[str] = set()
    group_orders: set[int] = set()
    lesson_ids: set[int] = set()

    for raw_group in raw_groups:
        if not isinstance(raw_group, dict):
            raise LessonCatalogError("Ders grubu yapısı geçersiz")
        group_id = _positive_int(raw_group.get("id"), "group.id")
        group_order = _non_negative_int(raw_group.get("order"), "group.order")
        name = _letters_and_spaces(raw_group.get("name"), "Ders grubu adı")
        if group_id in group_ids or name in group_names or group_order in group_orders:
            raise LessonCatalogError("Ders grubu kimliği, adı veya sırası yineleniyor")
        group_ids.add(group_id)
        group_names.add(name)
        group_orders.add(group_order)

        raw_lessons = raw_group.get("lessons")
        if not isinstance(raw_lessons, list) or not raw_lessons:
            raise LessonCatalogError(f"{name} grubunda ders bulunamadı")
        lessons: list[LessonEntry] = []
        lesson_orders: set[int] = set()
        for raw_lesson in raw_lessons:
            if not isinstance(raw_lesson, dict):
                raise LessonCatalogError("Ders metni yapısı geçersiz")
            lesson_id = _positive_int(raw_lesson.get("id"), "lesson.id")
            legacy_metin_id = _positive_int(
                raw_lesson.get("legacy_metin_id"), "lesson.legacy_metin_id"
            )
            lesson_order = _non_negative_int(raw_lesson.get("order"), "lesson.order")
            legacy_title = raw_lesson.get("legacy_title")
            if not isinstance(legacy_title, str):
                raise LessonCatalogError("Eski ders başlığı geçersiz")
            text = _letters_and_spaces(raw_lesson.get("text"), "Ders metni")
            if lesson_id in lesson_ids or lesson_order in lesson_orders:
                raise LessonCatalogError("Ders kimliği veya sırası yineleniyor")
            lesson_ids.add(lesson_id)
            lesson_orders.add(lesson_order)
            lessons.append(
                LessonEntry(
                    id=lesson_id,
                    legacy_metin_id=legacy_metin_id,
                    legacy_title=legacy_title,
                    order=lesson_order,
                    text=text,
                )
            )
        lessons.sort(key=lambda lesson: lesson.order)
        groups.append(
            LessonGroup(
                id=group_id,
                name=name,
                order=group_order,
                lessons=tuple(lessons),
            )
        )

    groups.sort(key=lambda group: group.order)
    return LessonCatalog(language="tr", groups=tuple(groups))
