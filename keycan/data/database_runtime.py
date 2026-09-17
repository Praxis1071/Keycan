"""Runtime compatibility and user-content management for Keycan."""

from __future__ import annotations

import json
from datetime import datetime

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key

_ORIGINAL_INIT = Database.__init__


def _ensure_default_snapshot(self: Database) -> None:
    self.conn.execute(
        """CREATE TABLE IF NOT EXISTS default_content_sources (
            source_id INTEGER PRIMARY KEY,
            display_name TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            custom_key TEXT NOT NULL DEFAULT ''
        )"""
    )
    self.conn.execute(
        """CREATE TABLE IF NOT EXISTS default_content_lessons (
            lesson_id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            legacy_metin_id INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            custom_order INTEGER NOT NULL DEFAULT 0
        )"""
    )
    source_count = self.conn.execute("SELECT COUNT(*) FROM default_content_sources").fetchone()[0]
    if source_count == 0:
        rows = self.conn.execute(
            "SELECT id,display_name,relative_path,custom_key FROM sources WHERE is_custom=0 ORDER BY id"
        ).fetchall()
        for row in rows:
            self.conn.execute("INSERT INTO default_content_sources VALUES (?,?,?,?)", row)
        lesson_rows = self.conn.execute(
            "SELECT id,source_id,legacy_metin_id,title,text,custom_order FROM lessons WHERE is_custom=0 ORDER BY source_id,legacy_metin_id,id"
        ).fetchall()
        for row in lesson_rows:
            self.conn.execute("INSERT INTO default_content_lessons VALUES (?,?,?,?,?,?)", row)
        self.conn.commit()


def _init(self: Database, path):
    _ORIGINAL_INIT(self, path)
    _ensure_default_snapshot(self)


def _sources(self: Database):
    rows = self.conn.execute(
        "SELECT id,display_name,is_custom FROM sources WHERE is_deleted=0 ORDER BY display_name COLLATE NOCASE,id"
    ).fetchall()
    visible = []
    for source_id, name, is_custom in rows:
        has_lessons = self.conn.execute(
            "SELECT 1 FROM lessons WHERE source_id=? AND is_deleted=0 LIMIT 1", (source_id,)
        ).fetchone()
        if has_lessons or is_custom:
            visible.append((source_id, clean_source_name(name), bool(is_custom)))
    visible.sort(key=lambda row: natural_sort_key(row[1]))
    result = []
    for number, (source_id, name, _is_custom) in enumerate(visible, 1):
        result.append((source_id, self._display_source_name(name, number)))
    return result


def _lessons(self: Database, source_id: int):
    rows = self.conn.execute(
        """SELECT id FROM lessons
           WHERE source_id=? AND is_deleted=0
           ORDER BY custom_order,legacy_metin_id,id""",
        (source_id,),
    ).fetchall()
    return [(lesson_id, f"Ders {index}") for index, (lesson_id,) in enumerate(rows, 1)]


def _managed_groups(self: Database):
    return self.conn.execute(
        """SELECT id,display_name,custom_key,is_custom
           FROM sources WHERE is_deleted=0
           ORDER BY display_name COLLATE NOCASE,id"""
    ).fetchall()


def _managed_lessons(self: Database, source_id: int):
    return self.conn.execute(
        """SELECT id,text,custom_key,custom_order,is_custom
           FROM lessons WHERE source_id=? AND is_deleted=0
           ORDER BY custom_order,legacy_metin_id,id""",
        (source_id,),
    ).fetchall()


def _rename_group(self: Database, source_id: int, name: str) -> None:
    name = self._validate_group_name(name)
    cursor = self.conn.execute(
        "UPDATE sources SET display_name=? WHERE id=? AND is_deleted=0", (name, source_id)
    )
    if cursor.rowcount != 1:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.commit()


def _delete_group(self: Database, source_id: int) -> None:
    cursor = self.conn.execute(
        "UPDATE sources SET is_deleted=1 WHERE id=? AND is_deleted=0", (source_id,)
    )
    if cursor.rowcount != 1:
        raise ValueError("Ders grubu bulunamadı")
    self.conn.execute("UPDATE lessons SET is_deleted=1 WHERE source_id=?", (source_id,))
    self.conn.commit()


def _create_lesson(self: Database, source_id: int, text: str) -> int:
    text = self._validate_text(text)
    valid = self.conn.execute(
        "SELECT 1 FROM sources WHERE id=? AND is_deleted=0", (source_id,)
    ).fetchone()
    if not valid:
        raise ValueError("Ders grubu bulunamadı")
    order = self.conn.execute(
        "SELECT COALESCE(MAX(custom_order),-1)+1 FROM lessons WHERE source_id=? AND is_deleted=0",
        (source_id,),
    ).fetchone()[0]
    import uuid
    key = uuid.uuid4().hex
    cursor = self.conn.execute(
        """INSERT INTO lessons(source_id,legacy_metin_id,title,text,is_custom,is_deleted,custom_order,custom_key)
           VALUES(?,0,'Ders',?,1,0,?,?)""",
        (source_id, text, order, key),
    )
    self.conn.commit()
    return int(cursor.lastrowid)


def _update_lesson(self: Database, lesson_id: int, text: str) -> None:
    text = self._validate_text(text)
    cursor = self.conn.execute(
        "UPDATE lessons SET text=? WHERE id=? AND is_deleted=0", (text, lesson_id)
    )
    if cursor.rowcount != 1:
        raise ValueError("Metin bulunamadı")
    self.conn.commit()


def _delete_lesson(self: Database, lesson_id: int) -> None:
    row = self.conn.execute(
        "SELECT source_id FROM lessons WHERE id=? AND is_deleted=0", (lesson_id,)
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    self.conn.execute("UPDATE lessons SET is_deleted=1 WHERE id=?", (lesson_id,))
    self.conn.commit()
    _normalize_order(self, int(row[0]))


def _move_lesson(self: Database, lesson_id: int, direction: int) -> None:
    if direction not in (-1, 1):
        raise ValueError("Geçersiz sıralama yönü")
    row = self.conn.execute(
        "SELECT source_id FROM lessons WHERE id=? AND is_deleted=0", (lesson_id,)
    ).fetchone()
    if not row:
        raise ValueError("Metin bulunamadı")
    source_id = int(row[0])
    rows = self.conn.execute(
        "SELECT id FROM lessons WHERE source_id=? AND is_deleted=0 ORDER BY custom_order,legacy_metin_id,id",
        (source_id,),
    ).fetchall()
    ids = [item[0] for item in rows]
    index = ids.index(lesson_id)
    target = index + direction
    if target < 0 or target >= len(ids):
        return
    ids[index], ids[target] = ids[target], ids[index]
    self.conn.execute("BEGIN")
    try:
        for order, item_id in enumerate(ids):
            self.conn.execute("UPDATE lessons SET custom_order=? WHERE id=?", (order, item_id))
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise


def _normalize_order(self: Database, source_id: int) -> None:
    rows = self.conn.execute(
        "SELECT id FROM lessons WHERE source_id=? AND is_deleted=0 ORDER BY custom_order,legacy_metin_id,id",
        (source_id,),
    ).fetchall()
    for order, (lesson_id,) in enumerate(rows):
        self.conn.execute("UPDATE lessons SET custom_order=? WHERE id=?", (order, lesson_id))
    self.conn.commit()


def _reset_all_content(self: Database):
    _ensure_default_snapshot(self)
    groups = self.conn.execute("SELECT COUNT(*) FROM sources WHERE is_deleted=0").fetchone()[0]
    lessons = self.conn.execute("SELECT COUNT(*) FROM lessons WHERE is_deleted=0").fetchone()[0]
    self.conn.execute("UPDATE lessons SET is_deleted=1 WHERE is_deleted=0")
    self.conn.execute("UPDATE sources SET is_deleted=1 WHERE is_deleted=0")
    self.conn.commit()
    return int(groups), int(lessons)


def _restore_defaults(self: Database):
    _ensure_default_snapshot(self)
    source_rows = self.conn.execute(
        "SELECT source_id,display_name,relative_path,custom_key FROM default_content_sources ORDER BY source_id"
    ).fetchall()
    lesson_rows = self.conn.execute(
        "SELECT lesson_id,source_id,legacy_metin_id,title,text,custom_order FROM default_content_lessons ORDER BY source_id,custom_order,lesson_id"
    ).fetchall()
    self.conn.execute("BEGIN")
    try:
        for source_id, name, relative_path, custom_key in source_rows:
            self.conn.execute(
                "UPDATE sources SET display_name=?,relative_path=?,custom_key=?,is_custom=0,is_deleted=0 WHERE id=?",
                (name, relative_path, custom_key, source_id),
            )
        default_ids = {row[0] for row in source_rows}
        if default_ids:
            placeholders = ",".join("?" for _ in default_ids)
            self.conn.execute(
                f"UPDATE lessons SET is_deleted=1 WHERE source_id IN ({placeholders})",
                tuple(default_ids),
            )
        for lesson_id, source_id, legacy_id, title, text, order in lesson_rows:
            self.conn.execute(
                """UPDATE lessons SET source_id=?,legacy_metin_id=?,title=?,text=?,is_custom=0,is_deleted=0,custom_order=? WHERE id=?""",
                (source_id, legacy_id, title, text, order, lesson_id),
            )
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise
    return len(source_rows), len(lesson_rows)


def _export_data(self: Database) -> str:
    groups = []
    for source_id, name, key, is_custom in self._managed_groups():
        lessons = [
            {"key": row[2], "text": row[1], "order": row[3]}
            for row in self._managed_lessons(source_id)
        ]
        groups.append({"key": key, "name": name, "lessons": lessons, "is_custom": bool(is_custom)})
    rows = self.conn.execute(
        """SELECT completed_at,duration_seconds,correct_words,wrong_words,words_per_minute,characters_per_minute,
                  target_word_count,typed_word_count,total_characters,correct_characters,wrong_characters,
                  accuracy_percent,source_name_snapshot,lesson_title_snapshot
           FROM practice_results WHERE completed_at!='' ORDER BY completed_at,rowid"""
    ).fetchall()
    fields=("completed_at","duration_seconds","correct_words","wrong_words","words_per_minute","characters_per_minute","target_word_count","typed_word_count","total_characters","correct_characters","wrong_characters","accuracy_percent","source_name","lesson_title")
    payload={"format":"keycan-backup","version":2,"exported_at":datetime.now().astimezone().isoformat(),"groups":groups,"practice_results":[dict(zip(fields,row)) for row in rows]}
    return json.dumps(payload,ensure_ascii=False,indent=2)


def _import_data(self: Database, raw: str):
    payload=json.loads(raw)
    if payload.get("format")!="keycan-backup" or payload.get("version") not in (1,2):
        raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
    groups=payload.get("groups",payload.get("custom_groups",[]))
    if not isinstance(groups,list): raise ValueError("Yedek dosyasının ders grup yapısı geçersiz")
    imported_groups=0; imported_lessons=0
    self.conn.execute("BEGIN")
    try:
        for group in groups:
            key=str(group.get("key","")).strip(); name=self._validate_group_name(str(group.get("name","")))
            if not key: raise ValueError("Ders grubu kimliği eksik")
            existing=self.conn.execute("SELECT id FROM sources WHERE custom_key=? AND is_deleted=0",(key,)).fetchone()
            if existing:
                source_id=int(existing[0]); self.conn.execute("UPDATE sources SET display_name=? WHERE id=?",(name,source_id))
            else:
                import uuid
                source_id=int(self.conn.execute("INSERT INTO sources(display_name,relative_path,is_custom,is_deleted,custom_key) VALUES(?, '', 1,0,?)",(name,key)).lastrowid)
            imported_groups+=1
            lessons=group.get("lessons",[])
            for order,item in enumerate(lessons):
                lesson_key=str(item.get("key","")).strip(); text=self._validate_text(str(item.get("text","")))
                if not lesson_key: raise ValueError("Metin kimliği eksik")
                found=self.conn.execute("SELECT id FROM lessons WHERE custom_key=?",(lesson_key,)).fetchone()
                if found:
                    lesson_id=int(found[0]); self.conn.execute("UPDATE lessons SET source_id=?,text=?,custom_order=?,is_deleted=0 WHERE id=?",(source_id,text,order,lesson_id))
                else:
                    lesson_id=int(self.conn.execute("INSERT INTO lessons(source_id,legacy_metin_id,title,text,is_custom,is_deleted,custom_order,custom_key) VALUES(?,0,'Ders',?,1,0,?,?)",(source_id,text,order,lesson_key)).lastrowid)
                imported_lessons+=1
        self.conn.commit()
    except Exception:
        self.conn.rollback(); raise
    return imported_groups, imported_lessons


def _patch():
    Database.__init__=_init
    Database.sources=_sources
    Database.lessons=_lessons
    Database.managed_groups=_managed_groups
    Database.managed_lessons=_managed_lessons
    Database.rename_group=_rename_group
    Database.delete_group=_delete_group
    Database.create_lesson=_create_lesson
    Database.update_lesson=_update_lesson
    Database.delete_lesson=_delete_lesson
    Database.move_lesson=_move_lesson
    Database.reset_all_content=_reset_all_content
    Database.restore_defaults=_restore_defaults
    Database.export_data=_export_data
    Database.import_data=_import_data


_patch()
