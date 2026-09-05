#!/usr/bin/env bash
# Keycan için zarar vermeyen stabilite ve veri bütünlüğü denetimleri.
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_dir"

python -m py_compile data_loader.py main.py

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

    result_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(practice_results)")
    }
    required_result_columns = {
        "lesson_id",
        "duration_seconds",
        "correct_words",
        "wrong_words",
        "words_per_minute",
        "characters_per_minute",
    }
    assert required_result_columns <= result_columns, "practice_results şeması eksik"

    invalid_durations = connection.execute(
        "SELECT COUNT(*) FROM practice_results WHERE duration_seconds < 0"
    ).fetchone()[0]
    assert invalid_durations == 0, "Negatif süreli sonuç bulundu"

    invalid_counts = connection.execute(
        """SELECT COUNT(*) FROM practice_results
           WHERE correct_words < 0 OR wrong_words < 0
              OR words_per_minute != 0 OR characters_per_minute != 0"""
    ).fetchone()[0]
    assert invalid_counts == 0, "Sonuçlarda geçersiz kelime/hız değeri bulundu"

    print(
        f"Veri denetimi başarılı: {sources} kaynak, {lessons} metin, "
        f"{statistics} eski istatistik."
    )
finally:
    connection.close()
PY

python -c 'from PyQt6 import QtCore; print(f"PyQt6: {QtCore.PYQT_VERSION_STR}")'

echo "Kod, veritabanı, sonuç şeması ve PyQt6 denetimleri başarılı."
