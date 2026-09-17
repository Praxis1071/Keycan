from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from keycan.data.database import Database
import keycan.data.database_runtime  # noqa: F401


def make_db(path: Path) -> Database:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE sources (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, relative_path TEXT NOT NULL DEFAULT '');
        CREATE TABLE lessons (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, legacy_metin_id INTEGER NOT NULL DEFAULT 0, title TEXT NOT NULL, text TEXT NOT NULL, FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE practice_results (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER NOT NULL, duration_seconds REAL NOT NULL, correct_chars INTEGER NOT NULL DEFAULT 0, wrong_chars INTEGER NOT NULL DEFAULT 0, wpm REAL NOT NULL DEFAULT 0, correct_words INTEGER NOT NULL DEFAULT 0, wrong_words INTEGER NOT NULL DEFAULT 0, words_per_minute REAL NOT NULL DEFAULT 0, characters_per_minute REAL NOT NULL DEFAULT 0);
        INSERT INTO sources VALUES (1, 'Hazır Ders', '');
        INSERT INTO lessons VALUES (1, 1, 1, 'Ders Test', 'hazır metin');
        """
    )
    connection.commit(); connection.close()
    return Database(path)


def test_custom_group_reorder_preserves_text(tmp_path: Path) -> None:
    db=make_db(tmp_path/"custom.db")
    try:
        group=db.create_custom_group("Python 101"); first=db.create_custom_lesson(group,"AAA"); second=db.create_custom_lesson(group,"BBB"); third=db.create_custom_lesson(group,"CCC")
        db.move_custom_lesson(third,-1); db.move_custom_lesson(third,-1)
        ordered=db.custom_lessons(group)
        assert [row[0] for row in ordered]==[third,first,second]
        assert [row[1] for row in ordered]==["CCC","AAA","BBB"]
        assert [name for source_id,name in db.sources() if source_id==group]==["Python 101"]
    finally: db.close()


def test_custom_group_delete_keeps_history_but_hides_content(tmp_path: Path) -> None:
    db=make_db(tmp_path/"delete.db")
    try:
        group=db.create_custom_group("Silinecek"); lesson=db.create_custom_lesson(group,"metin")
        db.save_result(lesson,60,1,0,target_word_count=1,typed_word_count=1,total_characters=5,correct_characters=5,wrong_characters=0,words_per_minute=1,characters_per_minute=5,accuracy_percent=100)
        db.delete_custom_group(group)
        assert all(source_id!=group for source_id,_ in db.sources())
        assert db.conn.execute("SELECT COUNT(*) FROM practice_results WHERE lesson_id=?",(lesson,)).fetchone()[0]==1
    finally: db.close()


def test_backup_round_trip_restores_custom_content_and_stats(tmp_path: Path) -> None:
    db=make_db(tmp_path/"source.db")
    try:
        group=db.create_custom_group("Yedek Grubu"); lesson=db.create_custom_lesson(group,"yedek metni")
        db.save_result(lesson,60,4,0,target_word_count=4,typed_word_count=4,total_characters=12,correct_characters=12,wrong_characters=0,words_per_minute=4,characters_per_minute=12,accuracy_percent=100)
        backup=db.export_data()
    finally: db.close()
    restored=make_db(tmp_path/"restored.db")
    try:
        imported,skipped=restored.import_data(backup)
        assert imported==1 and skipped==0
        groups=restored.custom_groups(); assert len(groups)==1
        lessons=restored.custom_lessons(groups[0][0]); assert [row[1] for row in lessons]==["yedek metni"]
        assert restored.practice_statistics("Tümü")["practices"]==1
        json.loads(restored.export_data())
    finally: restored.close()
