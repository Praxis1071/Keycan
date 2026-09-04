#!/usr/bin/env python3
"""MDBTools ile eski ders veritabanlarını SQLite'a kayıpsız aktarır."""

from __future__ import annotations

import argparse
import csv
import io
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    legacy_metin_id INTEGER,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(source_id, legacy_metin_id)
);

CREATE TABLE IF NOT EXISTS legacy_statistics (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    legacy_istatistik_id INTEGER,
    legacy_metin_id INTEGER,
    recorded_at TEXT,
    correct_value TEXT,
    wrong_value TEXT,
    total_value TEXT
);

CREATE TABLE IF NOT EXISTS practice_results (
    id INTEGER PRIMARY KEY,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL NOT NULL,
    correct_chars INTEGER NOT NULL DEFAULT 0,
    wrong_chars INTEGER NOT NULL DEFAULT 0,
    wpm REAL NOT NULL DEFAULT 0,
    correct_words INTEGER NOT NULL DEFAULT 0,
    wrong_words INTEGER NOT NULL DEFAULT 0,
    words_per_minute REAL NOT NULL DEFAULT 0,
    characters_per_minute REAL NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_lessons_source ON lessons(source_id);
CREATE INDEX IF NOT EXISTS idx_results_lesson ON practice_results(lesson_id);
"""

# Eski derslerin bir bölümünde yazım metninin parçası olmayan kurum etiketi
# bulunur. Yalnızca metnin en başındaysa kaldırılır; metnin geri kalanı aynen
# korunur. "KLAYVE" eski veri içindeki olası yazım biçimini de kapsar.
COURSE_PREFIX = re.compile(
    r"^\s*\[ÖZCAN[^\]]*(?:KLAVYE|KLAYVE)[^\]]*\]\s*", re.IGNORECASE
)

# Eski kaynak klasörlerinin kökünde bulunan gereksiz proje klasörü adı.
# Konu adının kendisine dokunulmaz; yalnızca baştaki prefix kaldırılır.
SOURCE_PREFIX = re.compile(r"^REVERSE ENGINEERING[/\\]+", re.IGNORECASE)


def clean_lesson_text(text: str) -> str:
    return COURSE_PREFIX.sub("", text, count=1)


def clean_source_path(path: str) -> str:
    """Kaynak yolunun başındaki gereksiz REVERSE ENGINEERING prefixini kaldırır."""
    return SOURCE_PREFIX.sub("", path, count=1)


def export_rows(mdb_path: Path, table: str) -> list[dict[str, str]]:
    """mdb-export CSV çıktısını okur; metin alanlarında hiçbir temizleme yapmaz."""
    # Varsayılan çıktı başlık satırını içerir; -H seçeneği bunu kaldırdığı için
    # burada özellikle kullanılmaz.
    command = ["mdb-export", str(mdb_path), table]
    result = subprocess.run(command, capture_output=True, check=True)
    output = result.stdout.decode("utf-8", errors="strict")
    return list(csv.DictReader(io.StringIO(output)))


def display_name(relative_mdb_path: Path) -> str:
    # dBase.mdb yerine onu barındıran ders klasörünün anlaşılır adını kullan.
    return clean_source_path(str(relative_mdb_path.parent))


def import_database(conn: sqlite3.Connection, root: Path, mdb_path: Path) -> tuple[int, int]:
    relative_path = clean_source_path(str(mdb_path.relative_to(root)))
    source = conn.execute(
        "INSERT INTO sources(relative_path, display_name) VALUES (?, ?)",
        (relative_path, display_name(Path(str(mdb_path.relative_to(root))))),
    )
    source_id = source.lastrowid

    lesson_rows = export_rows(mdb_path, "TBL_METIN")
    for row in lesson_rows:
        # MDB içeriği aynen saklanır; boş başlıklar arayüzde anlamlı bir ad alır.
        legacy_id = row.get("MetinID") or None
        title = row.get("MetinBaslik") or f"Metin {legacy_id or ''}".strip()
        text = clean_lesson_text(row.get("Metin") or "")
        conn.execute(
            """INSERT INTO lessons(source_id, legacy_metin_id, title, text)
               VALUES (?, ?, ?, ?)""",
            (source_id, legacy_id, title, text),
        )

    statistics_rows = export_rows(mdb_path, "TBL_ISTATISTIK")
    for row in statistics_rows:
        conn.execute(
            """INSERT INTO legacy_statistics(
                    source_id, legacy_istatistik_id, legacy_metin_id, recorded_at,
                    correct_value, wrong_value, total_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                row.get("IstatistikID") or None,
                row.get("MetinID") or None,
                row.get("TarihSaat") or None,
                row.get("Dogru") or None,
                row.get("Yanlis") or None,
                row.get("Toplam") or None,
            ),
        )
    return len(lesson_rows), len(statistics_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="Eski ders klasörlerinin kökü")
    parser.add_argument(
        "--output", type=Path, default=Path("typing_data.db"), help="SQLite çıktı yolu"
    )
    args = parser.parse_args()
    root = args.source_root.resolve()
    mdb_files = sorted(root.rglob("dBase.mdb"))
    if not mdb_files:
        parser.error(f"{root} altında dBase.mdb bulunamadı")

    output = args.output.resolve()
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(output)
    try:
        conn.executescript(SCHEMA)
        lesson_count = stats_count = 0
        with conn:
            for index, mdb_path in enumerate(mdb_files, start=1):
                lessons, stats = import_database(conn, root, mdb_path)
                lesson_count += lessons
                stats_count += stats
                print(f"[{index:02}/{len(mdb_files)}] {mdb_path.relative_to(root)}: {lessons} metin")
        print(
            f"\nTamamlandı: {len(mdb_files)} kaynak, {lesson_count} metin, "
            f"{stats_count} eski istatistik → {output}"
        )
    except (subprocess.CalledProcessError, UnicodeDecodeError) as error:
        conn.rollback()
        print(f"Aktarım başarısız: {error}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
