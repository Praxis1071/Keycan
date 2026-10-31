from __future__ import annotations

import json
from pathlib import Path

import pytest

from keycan.services.lesson_catalog import LessonCatalogError, load_lesson_catalog


def test_default_catalog_has_expected_groups_and_lessons() -> None:
    catalog = load_lesson_catalog()
    assert catalog.language == "tr"
    assert len(catalog.groups) == 82
    assert sum(len(group.lessons) for group in catalog.groups) == 1833


def test_default_catalog_names_and_texts_contain_only_letters_and_spaces() -> None:
    catalog = load_lesson_catalog()
    names = [group.name for group in catalog.groups]
    assert len(names) == len(set(names))
    for group in catalog.groups:
        assert group.name == " ".join(group.name.split())
        assert all(character.isalpha() or character == " " for character in group.name)
        for lesson in group.lessons:
            assert lesson.text
            assert lesson.text == " ".join(lesson.text.split())
            assert all(character.isalpha() or character == " " for character in lesson.text)


def test_catalog_rejects_duplicate_group_names(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "catalog_id": "test",
        "language": "tr",
        "groups": [
            {"id": 1, "name": "Temel Ders", "legacy_name": "Eski Temel Ders", "order": 0, "lessons": [
                {"id": 1, "legacy_metin_id": 1, "legacy_title": "1", "order": 0, "text": "temel ders"}
            ]},
            {"id": 2, "name": "Temel Ders", "legacy_name": "Eski Temel Ders", "order": 1, "lessons": [
                {"id": 2, "legacy_metin_id": 2, "legacy_title": "2", "order": 0, "text": "ikinci ders"}
            ]},
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(LessonCatalogError, match="yineleniyor"):
        load_lesson_catalog(path)


def test_catalog_rejects_numbers_and_punctuation_in_lesson_text(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "catalog_id": "test",
        "language": "tr",
        "groups": [
            {"id": 1, "name": "Temel Ders", "legacy_name": "Eski Temel Ders", "order": 0, "lessons": [
                {"id": 1, "legacy_metin_id": 1, "legacy_title": "1", "order": 0, "text": "merhaba 2026!"}
            ]},
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(LessonCatalogError, match="Ders metni"):
        load_lesson_catalog(path)
