#!/usr/bin/env bash
# Uygulama ve veritabanı için zarar vermeyen ön denetimler.
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_dir"

python -m py_compile data_loader.py main.py

python - <<'PY'
import sqlite3

connection = sqlite3.connect("typing_data.db")
try:
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    sources = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    lessons = connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
    assert connection.execute("SELECT COUNT(*) FROM lessons WHERE text = ''").fetchone()[0] == 0
    print(f"Veri denetimi başarılı: {sources} kaynak, {lessons} metin.")
finally:
    connection.close()
PY

python -c 'from PyQt6 import QtCore; print(f"PyQt6: {QtCore.PYQT_VERSION_STR}")'

echo "Kod, veritabanı ve PyQt6 denetimleri başarılı."
