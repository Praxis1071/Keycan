#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_dir"

command -v pyinstaller >/dev/null || { echo 'PyInstaller bulunamadı.' >&2; exit 1; }
if command -v appimagetool >/dev/null; then
  appimagetool_command=(appimagetool)
elif [[ -x tools/appimagetool-x86_64.AppImage ]]; then
  # CachyOS'ta FUSE kurulu olmasa da AppImage aracını çalıştırır.
  appimagetool_command=(env APPIMAGE_EXTRACT_AND_RUN=1 tools/appimagetool-x86_64.AppImage)
else
  echo 'appimagetool bulunamadı. tools/appimagetool-x86_64.AppImage ekleyin.' >&2
  exit 1
fi
python -c 'from PyQt6 import QtCore; print(QtCore.PYQT_VERSION_STR)' >/dev/null || {
  echo 'PyQt6 bu Python ortamında kurulu değil.' >&2
  exit 1
}
test -f typing_data.db || { echo 'Önce data_loader.py ile typing_data.db oluşturun.' >&2; exit 1; }
test -s tools/runtime-x86_64 || {
  echo 'tools/runtime-x86_64 AppImage çalışma zamanı eksik.' >&2
  exit 1
}

rm -rf build dist AppDir
pyinstaller --noconfirm --clean --onedir --windowed --name DakikaProgramlari \
  --add-data 'typing_data.db:.' main.py

# Sistemde eksik libjxrglue bağımlılığı olan, uygulamanın kullanmadığı JPEG XR
# görüntü eklentisini pakete dahil etme.
find dist/DakikaProgramlari -name 'kimg_jxr.so' -delete

mkdir -p AppDir/usr/bin AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/scalable/apps
cp -a dist/DakikaProgramlari/. AppDir/usr/bin/
cp DakikaProgramlari.desktop AppDir/usr/share/applications/

# Uygulama ile birlikte gelen SVG ikon kullanılır.
test -f dakika-programlari.svg || {
  echo 'dakika-programlari.svg ikonu eksik.' >&2
  exit 1
}
cp dakika-programlari.svg AppDir/usr/share/icons/hicolor/scalable/apps/
ln -s usr/share/icons/hicolor/scalable/apps/dakika-programlari.svg AppDir/dakika-programlari.svg
ln -s usr/share/applications/DakikaProgramlari.desktop AppDir/DakikaProgramlari.desktop

cat > AppDir/AppRun <<'EOF'
#!/usr/bin/env bash
HERE=$(dirname "$(readlink -f "$0")")
exec "$HERE/usr/bin/DakikaProgramlari" "$@"
EOF
chmod +x AppDir/AppRun

ARCH=x86_64 "${appimagetool_command[@]}" --runtime-file tools/runtime-x86_64 \
  AppDir "DakikaProgramlari-x86_64.AppImage"
