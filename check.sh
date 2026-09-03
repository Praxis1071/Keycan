#!/usr/bin/env bash
# Uygulama ve aktarılmış veri için zarar vermeyen ön denetimler.
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_dir"

python -m py_compile data_loader.py main.py
python - <<'PY'
import sqlite3

connection = sqlite3.connect("typing_data.db")
assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
sources = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
lessons = connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
assert sources == 83, sources
assert lessons == 1833, lessons
assert connection.execute("SELECT COUNT(*) FROM lessons WHERE text = ''").fetchone()[0] == 0
connection.close()
print(f"Veri denetimi başarılı: {sources} kaynak, {lessons} metin.")
PY

python -c 'from PyQt6 import QtCore; print(f"PyQt6: {QtCore.PYQT_VERSION_STR}")'
if command -v appimagetool >/dev/null; then
  :
elif [[ -x tools/appimagetool-x86_64.AppImage ]]; then
  APPIMAGE_EXTRACT_AND_RUN=1 tools/appimagetool-x86_64.AppImage --version >/dev/null
else
  echo 'appimagetool bulunamadı.' >&2
  exit 1
fi
test -s tools/runtime-x86_64
echo "Arayüz ve AppImage araçları hazır. ./build.sh ile paketlenebilir."
