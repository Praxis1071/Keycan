from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from keycan.data.database import Database
import keycan.data.database_runtime  # noqa: F401
from keycan.services.lesson_service import LessonService


@pytest.fixture
def database(tmp_path: Path) -> Database:
    source = Path(__file__).resolve().parents[1] / "typing_data.db"
    target = tmp_path / "typing_data.db"
    shutil.copy2(source, target)
    db = Database(target)
    try:
        yield db
    finally:
        db.close()


def test_catalog_covers_every_bundled_default_id(database: Database) -> None:
    service = LessonService(database)
    coverage = service.coverage()

    assert coverage.complete
    assert len(service.catalog.groups) == 82
    assert sum(len(group.lessons) for group in service.catalog.groups) == 1833


def test_service_uses_clean_catalog_content_without_rewriting_sqlite(database: Database) -> None:
    service = LessonService(database)
    group = service.catalog.groups[0]
    lesson = group.lessons[0]

    original_group_name = database.conn.execute(
        "SELECT display_name FROM sources WHERE id = ?", (group.id,)
    ).fetchone()[0]
    original_text = database.conn.execute(
        "SELECT text FROM lessons WHERE id = ?", (lesson.id,)
    ).fetchone()[0]

    assert service.lesson(lesson.id)[2] == lesson.text
    assert any(
        group_id == group.id and name.endswith(group.name)
        for group_id, name in service.sources()
    )
    assert database.conn.execute(
        "SELECT display_name FROM sources WHERE id = ?", (group.id,)
    ).fetchone()[0] == original_group_name
    assert database.conn.execute(
        "SELECT text FROM lessons WHERE id = ?", (lesson.id,)
    ).fetchone()[0] == original_text


def test_service_preserves_user_renames_and_lesson_edits(database: Database) -> None:
    service = LessonService(database)
    group = service.catalog.groups[0]
    lesson = group.lessons[0]
    renamed = "Kullanici Grubu"
    edited = "kullanici tarafindan degistirilen metin"

    database.rename_group(group.id, renamed)
    database.update_lesson(lesson.id, edited)

    assert next(row[1] for row in service.managed_groups() if row[0] == group.id) == renamed
    assert service.lesson(lesson.id)[2] == edited
    assert next(row[1] for row in service.managed_lessons(group.id) if row[0] == lesson.id) == edited


def test_service_preserves_custom_groups_and_lessons(database: Database) -> None:
    service = LessonService(database)
    group_id = database.create_custom_group("Kendi Derslerim")
    lesson_id = database.create_custom_lesson(group_id, "benim ozel metnim")

    assert any(row[0] == group_id and row[1] == "Kendi Derslerim" for row in service.managed_groups())
    assert service.lesson(lesson_id)[2] == "benim ozel metnim"
    assert any(row[0] == lesson_id and row[1] == "benim ozel metnim" for row in service.managed_lessons(group_id))


def test_service_resolves_all_built_in_texts_to_catalog(database: Database) -> None:
    service = LessonService(database)
    for group in service.catalog.groups:
        rows = service.managed_lessons(group.id)
        resolved = {row[0]: row[1] for row in rows}
        default_order = [row[0] for row in rows if not row[4]]
        assert default_order == [lesson.id for lesson in group.lessons]
        for lesson in group.lessons:
            assert resolved[lesson.id] == lesson.text


def test_service_preserves_catalog_group_order(database: Database) -> None:
    service = LessonService(database)
    catalog_ids = {group.id for group in service.catalog.groups}
    visible_default_ids = [
        group_id for group_id, _name in service.sources() if group_id in catalog_ids
    ]
    expected = [group.id for group in service.catalog.groups]
    assert visible_default_ids == expected



def test_service_falls_back_to_sqlite_when_catalog_is_unavailable(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from keycan.services.lesson_catalog import LessonCatalogError

    def unavailable():
        raise LessonCatalogError("Ders kataloğu JSON biçimi geçersiz")

    monkeypatch.setattr("keycan.services.lesson_service.load_lesson_catalog", unavailable)
    service = LessonService(database)

    assert service.catalog_error == "Ders kataloğu JSON biçimi geçersiz"
    assert service.sources() == database.sources()
    first_lesson_id = database.lessons(1)[0][0]
    assert service.lesson(first_lesson_id) == database.lesson(first_lesson_id)
