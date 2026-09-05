#!/usr/bin/env python3
"""Keycan GTK4/libadwaita arayüzü.

Mevcut PyQt6 sürümündeki veri ve yazma davranışını koruyan Stage 6 arayüzüdür.
"""

from __future__ import annotations

import html
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, GLib, Gtk


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB = APP_DIR / "typing_data.db"
SOURCE_PREFIX = re.compile(r"^REVERSE ENGINEERING[/\\]+", re.IGNORECASE)
WORD_PATTERN = re.compile(r"\S+")


def clean_source_name(name: str) -> str:
    return SOURCE_PREFIX.sub("", name, count=1)


def natural_sort_key(value: str) -> list[object]:
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def format_remaining(seconds: float) -> str:
    remaining = max(0, int(seconds + 0.999))
    minutes, seconds = divmod(remaining, 60)
    return f"{minutes:02d}:{seconds:02d}"


def normalize_word(word: str) -> str:
    return "".join(
        char.casefold()
        for char in word
        if not unicodedata.category(char).startswith("P")
    )


class Database:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self._migrate_results_schema()

    def _migrate_results_schema(self) -> None:
        columns = {
            row[1] for row in self.conn.execute("PRAGMA table_info(practice_results)")
        }
        additions = {
            "correct_words": "INTEGER NOT NULL DEFAULT 0",
            "wrong_words": "INTEGER NOT NULL DEFAULT 0",
            "words_per_minute": "REAL NOT NULL DEFAULT 0",
            "characters_per_minute": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.conn.execute(
                    f"ALTER TABLE practice_results ADD COLUMN {name} {definition}"
                )
        self.conn.commit()

    def sources(self) -> list[tuple[int, str]]:
        rows = self.conn.execute("SELECT id, display_name FROM sources").fetchall()
        cleaned = [(source_id, clean_source_name(name)) for source_id, name in rows]
        return sorted(cleaned, key=lambda row: natural_sort_key(row[1]))

    def lessons(self, source_id: int) -> list[tuple[int, str]]:
        rows = self.conn.execute(
            "SELECT id, title FROM lessons WHERE source_id = ? ORDER BY legacy_metin_id, id",
            (source_id,),
        ).fetchall()
        return [(lesson_id, f"Ders {index}") for index, (lesson_id, _) in enumerate(rows, 1)]

    def lesson(self, lesson_id: int) -> tuple[int, str, str]:
        row = self.conn.execute(
            "SELECT id, title, text FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        return row

    def save_result(self, lesson_id: int, duration: float, correct: int, wrong: int) -> None:
        self.conn.execute(
            """INSERT INTO practice_results(
                lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                correct_words, wrong_words, words_per_minute, characters_per_minute
            ) VALUES (?, ?, 0, 0, 0, ?, ?, 0, 0)""",
            (lesson_id, duration, correct, wrong),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


CSS = """
headerbar.keycan-header {
    background: #202124;
    color: #f2f2f2;
}
headerbar.keycan-header windowhandle,
headerbar.keycan-header button,
headerbar.keycan-header label {
    color: #f2f2f2;
}
.keycan-content {
    background: #202124;
}
.keycan-controls {
    background: #202124;
}
.keycan-controls label {
    color: #eeeeee;
}
.keycan-editor {
    background: #ffffff;
    color: #111111;
    border: 1px solid #b8b8b8;
}
.keycan-editor textview,
.keycan-editor textview text {
    background: #ffffff;
    color: #111111;
}
.keycan-editor textview {
    padding: 10px;
}
.keycan-status {
    color: #eeeeee;
    padding: 4px 2px 8px;
}
.keycan-countdown {
    color: #eeeeee;
    font-weight: 700;
    font-size: 16px;
}
"""


class KeycanWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, database_path: Path) -> None:
        super().__init__(application=app, title="Keycan — On Parmak")
        self.set_default_size(1200, 760)
        self.set_size_request(900, 600)
        self.db = Database(database_path)
        self.current_lesson_id: int | None = None
        self.current_text = ""
        self.typed = ""
        self.finished = False
        self.started_at: float | None = None
        self.updating_input = False
        self.tick_id: int | None = None

        self._install_css()
        self._build_ui()
        self._load_sources()
        self.connect("close-request", self._on_close_request)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS, -1)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self) -> None:
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.add_css_class("keycan-header")
        toolbar.add_top_bar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.add_css_class("keycan-content")
        toolbar.set_content(root)
        self.set_content(toolbar)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.set_margin_top(10)
        controls.set_margin_start(12)
        controls.set_margin_end(12)
        controls.set_margin_bottom(8)
        controls.add_css_class("keycan-controls")
        root.append(controls)

        controls.append(self._label("Ders grubu:"))
        self.source_dropdown = Gtk.DropDown()
        self.source_dropdown.set_hexpand(True)
        self.source_dropdown.connect("notify::selected", self._on_source_changed)
        controls.append(self.source_dropdown)

        controls.append(self._label("Metin:"))
        self.lesson_dropdown = Gtk.DropDown()
        self.lesson_dropdown.set_size_request(190, -1)
        self.lesson_dropdown.connect("notify::selected", self._on_lesson_changed)
        controls.append(self.lesson_dropdown)

        controls.append(self._label("Süre:"))
        adjustment = Gtk.Adjustment(value=1, lower=1, upper=180, step_increment=1, page_increment=10)
        self.duration_spin = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        self.duration_spin.set_numeric(True)
        self.duration_spin.set_width_chars(3)
        self.duration_spin.connect("value-changed", self._on_duration_changed)
        controls.append(self.duration_spin)
        controls.append(self._label("dakika"))

        self.countdown = Gtk.Label(label="01:00")
        self.countdown.add_css_class("keycan-countdown")
        self.countdown.set_margin_start(2)
        controls.append(self.countdown)

        self.restart_button = Gtk.Button(label="Baştan Başla")
        self.restart_button.add_css_class("suggested-action")
        self.restart_button.connect("clicked", self._restart)
        controls.append(self.restart_button)

        editors = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        editors.set_vexpand(True)
        editors.set_wide_handle(True)
        editors.set_margin_start(12)
        editors.set_margin_end(12)
        editors.set_margin_bottom(8)
        root.append(editors)

        self.target_view = self._make_text_view(False, 16)
        self.target_scroll = self._wrap_editor(self.target_view)
        editors.set_start_child(self.target_scroll)

        self.input_view = self._make_text_view(True, 16)
        self.input_view.set_monospace(True)
        self.input_view.get_buffer().connect("changed", self._on_input_changed)
        self.input_scroll = self._wrap_editor(self.input_view)
        editors.set_end_child(self.input_scroll)
        editors.set_position(470)

        self.status = Gtk.Label(label="Bir ders ve metin seçin.")
        self.status.set_xalign(0)
        self.status.add_css_class("keycan-status")
        self.status.set_margin_start(12)
        self.status.set_margin_end(12)
        root.append(self.status)

    @staticmethod
    def _label(text: str) -> Gtk.Label:
        label = Gtk.Label(label=text)
        label.set_xalign(0)
        return label

    @staticmethod
    def _make_text_view(editable: bool, size: int) -> Gtk.TextView:
        view = Gtk.TextView()
        view.set_editable(editable)
        view.set_cursor_visible(editable)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.set_vexpand(True)
        view.set_hexpand(True)
        view.set_pixels_above_lines(1)
        view.set_pixels_below_lines(1)
        view.set_left_margin(8)
        view.set_right_margin(8)
        view.set_top_margin(8)
        view.set_bottom_margin(8)
        font = "Noto Sans 16" if not editable else "Noto Sans Mono 16"
        view.set_css_name("textview")
        view.set_tooltip_text(None)
        provider = Gtk.CssProvider()
        provider.load_from_data(f"textview {{ font: {font}; }}", -1)
        view.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        return view

    @staticmethod
    def _wrap_editor(view: Gtk.TextView) -> Gtk.ScrolledWindow:
        frame = Gtk.Frame()
        frame.add_css_class("keycan-editor")
        frame.set_child(view)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(frame)
        scroll.set_vexpand(True)
        return scroll

    def _load_sources(self) -> None:
        sources = self.db.sources()
        names = [name for _, name in sources]
        self.source_ids = [source_id for source_id, _ in sources]
        self.source_dropdown.set_model(Gtk.StringList.new(names))
        if names:
            self.source_dropdown.set_selected(0)

    def _load_lessons(self, source_id: int) -> None:
        lessons = self.db.lessons(source_id)
        self.lesson_ids = [lesson_id for lesson_id, _ in lessons]
        self.lesson_dropdown.set_model(Gtk.StringList.new([title for _, title in lessons]))
        if lessons:
            self.lesson_dropdown.set_selected(0)
        else:
            self.current_lesson_id = None
            self.current_text = ""
            self._restart()

    def _on_source_changed(self, _dropdown: Gtk.DropDown, _param) -> None:  # type: ignore[no-untyped-def]
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids):
            self._load_lessons(self.source_ids[index])

    def _on_lesson_changed(self, _dropdown: Gtk.DropDown, _param) -> None:  # type: ignore[no-untyped-def]
        index = self.lesson_dropdown.get_selected()
        if 0 <= index < len(getattr(self, "lesson_ids", [])):
            lesson_id = self.lesson_ids[index]
            _id, _title, text = self.db.lesson(lesson_id)
            self.current_lesson_id = lesson_id
            self.current_text = text
            self._restart()

    def _on_duration_changed(self, _spin: Gtk.SpinButton) -> None:
        if self.started_at is None or self.finished:
            self.countdown.set_text(format_remaining(self._duration_seconds()))

    def _duration_seconds(self) -> int:
        return int(self.duration_spin.get_value()) * 60

    def _restart(self, _button: Gtk.Button | None = None) -> None:
        self.typed = ""
        self.finished = False
        self.started_at = None
        self.duration_spin.set_sensitive(True)
        self.countdown.set_text(format_remaining(self._duration_seconds()))
        self._set_input_text("")
        self._set_target_text(self.current_text)
        self.input_view.set_editable(self.current_lesson_id is not None)
        self.status.set_text("Yazmaya başlayınca geri sayım çalışır.") if self.current_lesson_id else self.status.set_text("Bir ders ve metin seçin.")
        if self.current_lesson_id:
            self.input_view.grab_focus()
        if self.tick_id is None:
            self.tick_id = GLib.timeout_add(100, self._check_time)

    def _set_input_text(self, text: str) -> None:
        self.updating_input = True
        self.input_view.get_buffer().set_text(text)
        self.updating_input = False

    def _set_target_text(self, text: str) -> None:
        self.target_view.get_buffer().set_text(text)

    def _on_input_changed(self, buffer: Gtk.TextBuffer) -> None:
        if self.updating_input or self.finished or self.current_lesson_id is None:
            return
        self.typed = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        if self.started_at is None and self.typed:
            self.started_at = time.monotonic()
            self.duration_spin.set_sensitive(False)
        if self.started_at is not None and time.monotonic() - self.started_at >= self._duration_seconds():
            self._finish()

    def _match_words(self) -> tuple[set[int], list[bool]]:
        target_matches = list(WORD_PATTERN.finditer(self.current_text))
        typed_matches = list(WORD_PATTERN.finditer(self.typed))
        unused = set(range(len(target_matches)))
        matched: set[int] = set()
        correctness: list[bool] = []
        for typed_match in typed_matches:
            typed_word = normalize_word(typed_match.group())
            target_index = next(
                (
                    index for index in sorted(unused)
                    if typed_word and normalize_word(target_matches[index].group()) == typed_word
                ),
                None,
            )
            if target_index is None:
                correctness.append(False)
            else:
                correctness.append(True)
                unused.remove(target_index)
                matched.add(target_index)
        return matched, correctness

    def _finish(self) -> None:
        if self.finished or self.current_lesson_id is None:
            return
        self.finished = True
        self.countdown.set_text("00:00")
        self.input_view.set_editable(False)
        self.duration_spin.set_sensitive(True)
        elapsed = 0.0 if self.started_at is None else min(time.monotonic() - self.started_at, self._duration_seconds())
        correct, wrong = self._render_results()
        self.db.save_result(self.current_lesson_id, elapsed, correct, wrong)
        self.status.set_text(f"Süre doldu. Doğru: {correct}  |  Yanlış: {wrong}  |  Toplam: {correct + wrong}")

    def _render_results(self) -> tuple[int, int]:
        matched, correctness = self._match_words()
        self._render_target_results(matched)
        self._render_input_results(correctness)
        correct = sum(correctness)
        return correct, len(correctness) - correct

    def _render_target_results(self, matched: set[int]) -> None:
        buffer = self.target_view.get_buffer()
        buffer.set_text(self.current_text)
        green = buffer.create_tag("correct-target", foreground="#16803c")
        target_matches = list(WORD_PATTERN.finditer(self.current_text))
        for index in matched:
            match = target_matches[index]
            start = buffer.get_iter_at_offset(match.start())
            end = buffer.get_iter_at_offset(match.end())
            buffer.apply_tag(green, start, end)

    def _render_input_results(self, correctness: list[bool]) -> None:
        buffer = self.input_view.get_buffer()
        green = buffer.create_tag("correct-input", foreground="#16803c")
        red = buffer.create_tag("wrong-input", foreground="#e01b24")
        matches = list(WORD_PATTERN.finditer(self.typed))
        for match, is_correct in zip(matches, correctness):
            start = buffer.get_iter_at_offset(match.start())
            end = buffer.get_iter_at_offset(match.end())
            buffer.apply_tag(green if is_correct else red, start, end)

    def _check_time(self) -> bool:
        if self.finished or self.started_at is None:
            return True
        remaining = self._duration_seconds() - (time.monotonic() - self.started_at)
        if remaining <= 0:
            self._finish()
        else:
            self.countdown.set_text(format_remaining(remaining))
        return True

    def _on_close_request(self, _window: Adw.ApplicationWindow) -> bool:
        if self.tick_id is not None:
            GLib.source_remove(self.tick_id)
            self.tick_id = None
        self.db.close()
        return False


class KeycanApplication(Adw.Application):
    def __init__(self, database_path: Path) -> None:
        super().__init__(application_id="org.keycan.Keycan")
        self.database_path = database_path
        self.window: KeycanWindow | None = None

    def do_activate(self) -> None:
        if self.window is None:
            self.window = KeycanWindow(self, self.database_path)
        self.window.present()


def main() -> int:
    database_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    if not database_path.exists():
        print(f"Veritabanı bulunamadı: {database_path}", file=sys.stderr)
        return 1
    return KeycanApplication(database_path).run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
