from __future__ import annotations

import sys
from pathlib import Path

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw

from keycan.window import KeycanWindow

APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = APP_DIR / "data" / "typing_data.db"


class KeycanApplication(Adw.Application):
    def __init__(self, database_path: Path) -> None:
        super().__init__(application_id="org.keycan.Keycan")
        self.database_path = database_path
        self.window: KeycanWindow | None = None

    def do_activate(self) -> None:
        if self.window is None:
            self.window = KeycanWindow(self, self.database_path)
        self.window.present()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv if argv is None else argv
    database_path = Path(args[1]) if len(args) > 1 else DEFAULT_DB
    if not database_path.exists():
        print(f"Veritabanı bulunamadı: {database_path}", file=sys.stderr)
        return 1
    return KeycanApplication(database_path).run(args)
