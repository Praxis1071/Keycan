#!/usr/bin/env bash
# Keycan 2.0 stabilite ve veri bütünlüğü denetimleri.
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_dir"

python -m py_compile main.py keycan/__init__.py keycan/app.py keycan/window.py keycan/core/__init__.py keycan/core/typing_engine.py keycan/data/__init__.py keycan/data/database.py keycan/data/database_compat2.py keycan/gui/content_manager2.py keycan/gui/settings2.py keycan/gui/statistics_clean.py keycan/gui/search.py keycan/gui/workspace.py tests/test_stage1_database.py tests/test_stage3_database.py tests/test_custom_content.py

python - <<'PY'
import sqlite3

connection = sqlite3.connect("typing_data.db")
try:
    connection.execute("PRAGMA foreign_keys = ON")
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    sources = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    lessons = connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
    statistics = connection.execute("SELECT COUNT(*) FROM legacy_statistics").fetchone()[0]

    assert sources > 0, "Kaynak bulunamadı"
    assert lessons > 0, "Ders bulunamadı"
    assert connection.execute("SELECT COUNT(*) FROM lessons WHERE text = ''").fetchone()[0] == 0
    assert connection.execute(
        "SELECT COUNT(*) FROM sources WHERE relative_path LIKE 'REVERSE ENGINEERING/%' "
        "OR relative_path LIKE 'REVERSE ENGINEERING\\\\%'"
    ).fetchone()[0] == 0, "Kaynak yolunda eski prefix kaldı"

    orphan_results = connection.execute(
        """SELECT COUNT(*) FROM practice_results AS r
           LEFT JOIN lessons AS l ON l.id = r.lesson_id
           WHERE l.id IS NULL"""
    ).fetchone()[0]
    assert orphan_results == 0, "Yetim practice_results kaydı bulundu"

    result_columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_results)")}
    required_result_columns = {
        "lesson_id", "duration_seconds", "correct_words", "wrong_words",
        "words_per_minute", "characters_per_minute", "completed_at",
        "source_name_snapshot", "lesson_title_snapshot", "target_word_count",
        "typed_word_count", "total_characters", "correct_characters",
        "wrong_characters", "accuracy_percent",
    }
    assert required_result_columns <= result_columns, "practice_results şeması eksik"

    user_columns = {row[1] for row in connection.execute("PRAGMA table_info(sources)")}
    lesson_user_columns = {row[1] for row in connection.execute("PRAGMA table_info(lessons)")}
    assert {"is_custom", "is_deleted", "custom_key"} <= user_columns, "sources kullanıcı şeması eksik"
    assert {"is_custom", "is_deleted", "custom_order", "custom_key"} <= lesson_user_columns, "lessons kullanıcı şeması eksik"

    invalid_durations = connection.execute("SELECT COUNT(*) FROM practice_results WHERE duration_seconds < 0").fetchone()[0]
    assert invalid_durations == 0, "Negatif süreli sonuç bulundu"
    invalid_counts = connection.execute(
        """SELECT COUNT(*) FROM practice_results
           WHERE correct_words < 0 OR wrong_words < 0 OR target_word_count < 0
              OR typed_word_count < 0 OR total_characters < 0 OR correct_characters < 0
              OR wrong_characters < 0 OR words_per_minute < 0 OR characters_per_minute < 0
              OR accuracy_percent < 0 OR accuracy_percent > 100"""
    ).fetchone()[0]
    assert invalid_counts == 0, "Sonuçlarda geçersiz çalışma değeri bulundu"
    inconsistent_character_counts = connection.execute(
        "SELECT COUNT(*) FROM practice_results WHERE total_characters != correct_characters + wrong_characters"
    ).fetchone()[0]
    assert inconsistent_character_counts == 0, "Karakter toplamları tutarsız"

    print(f"Veri denetimi başarılı: {sources} kaynak, {lessons} metin, {statistics} eski istatistik.")
finally:
    connection.close()
PY

python -m pytest -q tests/test_stage1_database.py tests/test_stage3_database.py tests/test_custom_content.py

echo "Keycan Python sözdizimi, veritabanı, sonuç şeması, Stage 3 ve kullanıcı içeriği denetimleri başarılı."
