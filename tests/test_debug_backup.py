from pathlib import Path
import json
from tests.test_custom_content import make_db


def test_debug_deleted_backup(tmp_path: Path):
    source = make_db(tmp_path / "src.db")
    source.save_result(
        1, 60, 1, 0, target_word_count=1, typed_word_count=1,
        total_characters=5, correct_characters=5, wrong_characters=0,
        words_per_minute=1, characters_per_minute=5, accuracy_percent=100,
    )
    source.delete_lesson(1)
    payload = json.loads(source.export_data())
    print("SOURCE PAYLOAD GROUP", payload["groups"][0])
    source.close()

    target = make_db(tmp_path / "dst.db")
    print("TARGET BEFORE", target.conn.execute("SELECT id,display_name,is_custom,is_deleted,custom_key FROM sources").fetchall())
    print("TARGET SNAPSHOT", target.conn.execute("SELECT * FROM default_content_sources").fetchall())
    print("TARGET LESSONS", target.conn.execute("SELECT id,source_id,text,is_custom,is_deleted,custom_key FROM lessons").fetchall())
    target.import_data(json.dumps(payload))
    print("TARGET AFTER SOURCES", target.conn.execute("SELECT id,display_name,is_custom,is_deleted,custom_key FROM sources").fetchall())
    print("TARGET AFTER LESSONS", target.conn.execute("SELECT id,source_id,text,is_custom,is_deleted,custom_key FROM lessons").fetchall())
    target.close()
    assert False, 'diagnostic output above'
