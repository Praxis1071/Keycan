"""Small runtime layer for the current database schema."""

from __future__ import annotations

import json
from datetime import datetime

from keycan.data.database import Database
from keycan.utils.text import clean_source_name, natural_sort_key


def _sources(self):
    rows=self.conn.execute("SELECT id,display_name,is_custom FROM sources WHERE is_deleted=0").fetchall()
    visible=[]
    for source_id,name,is_custom in rows:
        has=self.conn.execute("SELECT 1 FROM lessons WHERE source_id=? AND is_deleted=0 LIMIT 1",(source_id,)).fetchone()
        if has or is_custom: visible.append((source_id,clean_source_name(name),bool(is_custom)))
    visible.sort(key=lambda x:natural_sort_key(x[1])); result=[]; builtin=0
    for source_id,name,is_custom in visible:
        if is_custom: result.append((source_id,name))
        else:
            builtin+=1; result.append((source_id,self._display_source_name(name,builtin)))
    return result


def _lessons(self,source_id):
    row=self.conn.execute("SELECT is_custom FROM sources WHERE id=? AND is_deleted=0",(source_id,)).fetchone()
    if row and row[0]:
        rows=self.conn.execute("SELECT id FROM lessons WHERE source_id=? AND is_custom=1 AND is_deleted=0 ORDER BY custom_order,id",(source_id,)).fetchall()
        return [(lesson_id,str(i)) for i,(lesson_id,) in enumerate(rows,1)]
    rows=self.conn.execute("SELECT id FROM lessons WHERE source_id=? AND is_deleted=0 ORDER BY legacy_metin_id,id",(source_id,)).fetchall()
    return [(lesson_id,f"Ders {i}") for i,(lesson_id,) in enumerate(rows,1)]


def _import_data(self,raw):
    try: payload=json.loads(raw)
    except json.JSONDecodeError as exc: raise ValueError("Yedek dosyası geçerli JSON değil") from exc
    if not isinstance(payload,dict) or payload.get("format")!="keycan-backup" or payload.get("version")!=1: raise ValueError("Bu dosya Keycan yedeği değil veya desteklenmeyen bir sürüm kullanıyor")
    groups=payload.get("custom_groups",[]); results=payload.get("practice_results",[])
    if not isinstance(groups,list) or not isinstance(results,list): raise ValueError("Yedek dosyasının yapısı geçersiz")
    lesson_map={}; self.conn.execute("BEGIN")
    try:
        for group in groups:
            if not isinstance(group,dict): raise ValueError("Ders grubu kaydı geçersiz")
            key=str(group.get("key","")).strip(); name=self._validate_group_name(str(group.get("name","")))
            if not key: raise ValueError("Ders grubu kimliği eksik")
            existing=self.conn.execute("SELECT id FROM sources WHERE custom_key=? AND is_custom=1",(key,)).fetchone()
            if existing:
                source_id=int(existing[0]); self.conn.execute("UPDATE sources SET display_name=?,is_deleted=0 WHERE id=?",(name,source_id))
            else:
                source_id=int(self.conn.execute("INSERT INTO sources(display_name,relative_path,is_custom,is_deleted,custom_key) VALUES (?, '',1,0,?)",(name,key)).lastrowid)
            lessons=group.get("lessons",[])
            if not isinstance(lessons,list): raise ValueError("Ders grubu metin listesi geçersiz")
            for order,item in enumerate(lessons):
                if not isinstance(item,dict): raise ValueError("Metin kaydı geçersiz")
                lesson_key=str(item.get("key","")).strip(); text=self._validate_text(str(item.get("text","")))
                if not lesson_key: raise ValueError("Metin kimliği eksik")
                found=self.conn.execute("SELECT id FROM lessons WHERE custom_key=? AND is_custom=1",(lesson_key,)).fetchone()
                if found:
                    lesson_id=int(found[0]); self.conn.execute("UPDATE lessons SET source_id=?,text=?,title='Ders',custom_order=?,is_deleted=0 WHERE id=?",(source_id,text,order,lesson_id))
                else:
                    lesson_id=int(self.conn.execute("INSERT INTO lessons(source_id,legacy_metin_id,title,text,is_custom,is_deleted,custom_order,custom_key) VALUES (?,0,'Ders',?,1,0,?,?)",(source_id,text,order,lesson_key)).lastrowid)
                lesson_map[lesson_key]=lesson_id
        existing={tuple(row) for row in self.conn.execute("SELECT completed_at,lesson_id,duration_seconds,words_per_minute,typed_word_count,accuracy_percent FROM practice_results WHERE completed_at!=''").fetchall()}
        imported=skipped=0
        for item in results:
            if not isinstance(item,dict): skipped+=1; continue
            lesson_id=lesson_map.get(str(item.get("lesson_key","")).strip())
            if lesson_id is None:
                source_name=clean_source_name(str(item.get("source_name",""))); title=str(item.get("lesson_title",""))
                candidates=self.conn.execute("SELECT l.id,s.display_name,l.title FROM lessons l JOIN sources s ON s.id=l.source_id WHERE s.is_custom=0 AND s.is_deleted=0 AND l.is_deleted=0").fetchall()
                for cid,csource,ctitle in candidates:
                    if clean_source_name(csource)==source_name and ctitle==title: lesson_id=int(cid); break
            if lesson_id is None: skipped+=1; continue
            try:
                completed=str(item.get("completed_at","")); datetime.strptime(completed,"%Y-%m-%d %H:%M:%S")
                duration=float(item.get("duration_seconds",0)); correct=int(item.get("correct_words",0)); wrong=int(item.get("wrong_words",0)); wpm=float(item.get("words_per_minute",0)); cpm=float(item.get("characters_per_minute",0)); target=int(item.get("target_word_count",0)); typed=int(item.get("typed_word_count",0)); total=int(item.get("total_characters",0)); cc=int(item.get("correct_characters",0)); wc=int(item.get("wrong_characters",0)); accuracy=float(item.get("accuracy_percent",0))
            except (TypeError,ValueError): skipped+=1; continue
            if min(duration,correct,wrong,wpm,cpm,target,typed,total,cc,wc,accuracy)<0 or accuracy>100 or correct+wrong!=typed or total!=cc+wc: skipped+=1; continue
            fingerprint=(completed,lesson_id,duration,wpm,typed,accuracy)
            if fingerprint in existing: continue
            self.conn.execute("INSERT INTO practice_results(lesson_id,duration_seconds,correct_chars,wrong_chars,wpm,correct_words,wrong_words,words_per_minute,characters_per_minute,completed_at,source_name_snapshot,lesson_title_snapshot,target_word_count,typed_word_count,total_characters,correct_characters,wrong_characters,accuracy_percent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(lesson_id,duration,cc,wc,wpm,correct,wrong,wpm,cpm,completed,str(item.get("source_name","")),str(item.get("lesson_title","")),target,typed,total,cc,wc,accuracy)); existing.add(fingerprint); imported+=1
        self.conn.commit(); return imported,skipped
    except Exception:
        self.conn.rollback(); raise


Database.sources=_sources
Database.lessons=_lessons
Database.import_data=_import_data
