from __future__ import annotations

import time
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from keycan.core.typing_engine import TypingEngine
from keycan.data.database import Database
from keycan.utils.text import WORD_PATTERN, format_remaining


CSS = """
headerbar.keycan-header { background: #202124; color: #f2f2f2; }
headerbar.keycan-header windowhandle, headerbar.keycan-header button, headerbar.keycan-header label { color: #f2f2f2; }
.keycan-content, .keycan-controls { background: #202124; }
.keycan-controls label, .keycan-status { color: #eeeeee; }
.keycan-editor { background: #ffffff; color: #111111; border: 1px solid #b8b8b8; }
.keycan-editor textview, .keycan-editor textview text { background: #ffffff; color: #111111; }
.keycan-editor textview { padding: 10px; }
.keycan-status { padding: 2px 2px 4px; }
.keycan-countdown { color: #eeeeee; font-weight: 700; font-size: 16px; }
"""


class SettingsWindow(Adw.Window):
    def __init__(self, parent: "KeycanWindow") -> None:
        super().__init__(transient_for=parent, modal=True, title="Ayarlar")
        self.parent_window = parent
        self.set_default_size(460, 360)
        self.set_size_request(360, 280)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        for margin in ("top", "bottom", "start", "end"):
            getattr(content, f"set_margin_{margin}")(24)
        toolbar.set_content(content)
        self.set_content(toolbar)

        about = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        title = Gtk.Label(label="Hakkında")
        title.set_xalign(0); title.add_css_class("title-3"); about.append(title)
        developer = Gtk.Label(label="Geliştirici: Praxis1071")
        developer.set_xalign(0); about.append(developer)
        github = Gtk.LinkButton(uri="https://github.com/Praxis1071", label="GitHub profili: github.com/Praxis1071")
        github.set_halign(Gtk.Align.START); about.append(github); content.append(about)
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        privacy = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        label = Gtk.Label(label="Yazım metnini karart")
        label.set_xalign(0); label.set_hexpand(True); details.append(label)
        description = Gtk.Label(label="Yazarken kendi yazdığın metni gizler; süre bitince sonuçları gösterir.")
        description.set_xalign(0); description.set_wrap(True); description.add_css_class("dim-label"); details.append(description)
        privacy.append(details)
        self.privacy_switch = Gtk.Switch(); self.privacy_switch.set_valign(Gtk.Align.CENTER)
        self.privacy_switch.set_active(parent.privacy_enabled); self.privacy_switch.connect("notify::active", self._on_privacy_changed)
        privacy.append(self.privacy_switch); content.append(privacy)

    def _on_privacy_changed(self, switch: Gtk.Switch, _param) -> None:
        self.parent_window.privacy_enabled = switch.get_active()
        self.parent_window._apply_privacy_state()


class KeycanWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, database_path: Path) -> None:
        super().__init__(application=app, title="Keycan — On Parmak")
        self.set_default_size(1200, 760); self.set_size_request(900, 600)
        self.db = Database(database_path); self.engine = TypingEngine()
        self.current_lesson_id: int | None = None; self.current_text = ""; self.typed = ""
        self.finished = False; self.started_at: float | None = None; self.updating_input = False
        self.finish_pending = False; self.tick_id: int | None = None
        self.privacy_enabled = False; self.text_size = 16
        self.text_providers: dict[Gtk.TextView, Gtk.CssProvider] = {}; self.settings_window: SettingsWindow | None = None
        self._install_css(); self._build_ui(); self._load_sources(); self.connect("close-request", self._on_close_request)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider(); provider.load_from_data(CSS, -1)
        display = Gdk.Display.get_default()
        if display: Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_ui(self) -> None:
        toolbar = Adw.ToolbarView(); header = Adw.HeaderBar(); header.add_css_class("keycan-header"); toolbar.add_top_bar(header)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0); root.add_css_class("keycan-content"); toolbar.set_content(root); self.set_content(toolbar)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.set_margin_top(10); controls.set_margin_start(12); controls.set_margin_end(12); controls.set_margin_bottom(8); controls.add_css_class("keycan-controls"); root.append(controls)
        controls.append(self._label("Ders grubu:")); self.source_dropdown = Gtk.DropDown(); self.source_dropdown.set_hexpand(True); self.source_dropdown.connect("notify::selected", self._on_source_changed); controls.append(self.source_dropdown)
        controls.append(self._label("Metin:")); self.lesson_dropdown = Gtk.DropDown(); self.lesson_dropdown.set_size_request(190, -1); self.lesson_dropdown.connect("notify::selected", self._on_lesson_changed); controls.append(self.lesson_dropdown)
        controls.append(self._label("Süre:")); adj = Gtk.Adjustment(value=1, lower=1, upper=180, step_increment=1, page_increment=10)
        self.duration_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0); self.duration_spin.set_numeric(True); self.duration_spin.set_width_chars(3); self.duration_spin.connect("value-changed", self._on_duration_changed); controls.append(self.duration_spin); controls.append(self._label("dakika"))
        self.countdown = Gtk.Label(label="01:00"); self.countdown.add_css_class("keycan-countdown"); controls.append(self.countdown)
        self.restart_button = Gtk.Button(label="Baştan Başla"); self.restart_button.add_css_class("suggested-action"); self.restart_button.connect("clicked", self._restart); controls.append(self.restart_button)

        editors = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL); editors.set_vexpand(True); editors.set_wide_handle(True); editors.set_margin_start(12); editors.set_margin_end(12); editors.set_margin_bottom(4); root.append(editors)
        self.target_view = self._make_text_view(False, False); editors.set_start_child(self._wrap_editor(self.target_view))
        self.input_view = self._make_text_view(True, True); self.input_view.get_buffer().connect("changed", self._on_input_changed); editors.set_end_child(self._wrap_editor(self.input_view)); editors.set_position(470)

        bottom = Gtk.CenterBox(); bottom.set_margin_start(12); bottom.set_margin_end(12); bottom.set_size_request(-1, 34); root.append(bottom)
        self.status = Gtk.Label(label="Bir ders ve metin seçin."); self.status.set_xalign(0); self.status.add_css_class("keycan-status"); bottom.set_start_widget(self.status)
        self.settings_button = Gtk.Button(); self.settings_button.set_icon_name("emblem-system-symbolic"); self.settings_button.set_tooltip_text("Ayarlar"); self.settings_button.add_css_class("flat"); self.settings_button.connect("clicked", self._open_settings); bottom.set_center_widget(self.settings_button)
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); size_box.set_halign(Gtk.Align.END); size_box.append(Gtk.Label(label="Metin boyutu:"))
        size_adj = Gtk.Adjustment(value=self.text_size, lower=12, upper=30, step_increment=1, page_increment=2)
        self.size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1, digits=0); self.size_spin.set_numeric(True); self.size_spin.set_width_chars(3); self.size_spin.set_tooltip_text("Ders ve yazım metni boyutu"); self.size_spin.connect("value-changed", self._on_text_size_changed); size_box.append(self.size_spin); bottom.set_end_widget(size_box)

    @staticmethod
    def _label(text: str) -> Gtk.Label:
        label = Gtk.Label(label=text); label.set_xalign(0); return label

    def _make_text_view(self, editable: bool, monospace: bool) -> Gtk.TextView:
        view = Gtk.TextView(); view.set_editable(editable); view.set_cursor_visible(editable); view.set_monospace(monospace); view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); view.set_vexpand(True); view.set_hexpand(True)
        view.set_left_margin(8); view.set_right_margin(8); view.set_top_margin(8); view.set_bottom_margin(8); self._apply_text_size(view); return view

    def _apply_text_size(self, view: Gtk.TextView | None = None) -> None:
        views = [view] if view is not None else [self.target_view, self.input_view]
        for text_view in views:
            old = self.text_providers.get(text_view)
            if old is not None: text_view.get_style_context().remove_provider(old)
            provider = Gtk.CssProvider(); provider.load_from_data(f"textview {{ font-size: {self.text_size}px; }}", -1)
            text_view.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); self.text_providers[text_view] = provider

    def _on_text_size_changed(self, spin: Gtk.SpinButton) -> None:
        self.text_size = int(spin.get_value()); self._apply_text_size()

    @staticmethod
    def _wrap_editor(view: Gtk.TextView) -> Gtk.ScrolledWindow:
        frame = Gtk.Frame(); frame.add_css_class("keycan-editor"); frame.set_child(view)
        scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC); scroll.set_child(frame); scroll.set_vexpand(True); return scroll

    def _load_sources(self) -> None:
        sources = self.db.sources(); self.source_ids = [i for i, _ in sources]; self.source_dropdown.set_model(Gtk.StringList.new([n for _, n in sources]))
        if sources: self.source_dropdown.set_selected(0)

    def _load_lessons(self, source_id: int) -> None:
        lessons = self.db.lessons(source_id); self.lesson_ids = [i for i, _ in lessons]; self.lesson_dropdown.set_model(Gtk.StringList.new([n for _, n in lessons]))
        if lessons: self.lesson_dropdown.set_selected(0)
        else: self.current_lesson_id = None; self.current_text = ""; self._restart()

    def _on_source_changed(self, _dropdown: Gtk.DropDown, _param) -> None:
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids): self._load_lessons(self.source_ids[index])

    def _on_lesson_changed(self, _dropdown: Gtk.DropDown, _param) -> None:
        index = self.lesson_dropdown.get_selected()
        if 0 <= index < len(getattr(self, "lesson_ids", [])):
            lesson_id = self.lesson_ids[index]; _id, _title, text = self.db.lesson(lesson_id); self.current_lesson_id = lesson_id; self.current_text = text; self._restart()

    def _on_duration_changed(self, _spin: Gtk.SpinButton) -> None:
        if self.started_at is None or self.finished: self.countdown.set_text(format_remaining(self._duration_seconds()))

    def _duration_seconds(self) -> int: return int(self.duration_spin.get_value()) * 60

    def _restart(self, _button: Gtk.Button | None = None) -> None:
        self.typed = ""; self.finished = False; self.finish_pending = False; self.started_at = None; self.duration_spin.set_sensitive(True); self.countdown.set_text(format_remaining(self._duration_seconds()))
        self._set_input_text(""); self._set_target_text(self.current_text); self.input_view.set_editable(self.current_lesson_id is not None); self._apply_privacy_state()
        if self.current_lesson_id: self.status.set_text("Yazmaya başlayınca geri sayım çalışır."); self.input_view.grab_focus()
        else: self.status.set_text("Bir ders ve metin seçin.")
        if self.tick_id is None: self.tick_id = GLib.timeout_add(100, self._check_time)

    def _set_input_text(self, text: str) -> None:
        self.updating_input = True; self.input_view.get_buffer().set_text(text); self.updating_input = False

    def _set_target_text(self, text: str) -> None: self.target_view.get_buffer().set_text(text)

    @staticmethod
    def _get_tag(buffer: Gtk.TextBuffer, name: str, foreground: str) -> Gtk.TextTag:
        table = buffer.get_tag_table(); tag = table.lookup(name)
        if tag is None: tag = buffer.create_tag(name, foreground=foreground)
        return tag

    def _apply_privacy_state(self) -> None:
        active = self.privacy_enabled and self.started_at is not None and not self.finished; buffer = self.input_view.get_buffer(); hidden = self._get_tag(buffer, "privacy-hidden", "#ffffff"); hidden.set_priority(max(0, buffer.get_tag_table().get_size() - 1)); self.input_view.remove_css_class("keycan-hidden")
        start, end = buffer.get_start_iter(), buffer.get_end_iter()
        if active: buffer.remove_all_tags(start, end); buffer.apply_tag(hidden, start, end); self.input_view.set_cursor_visible(False)
        else: buffer.remove_tag(hidden, start, end); self.input_view.set_cursor_visible(not self.finished and self.current_lesson_id is not None)

    def _on_input_changed(self, buffer: Gtk.TextBuffer) -> None:
        if self.updating_input or self.finished or self.current_lesson_id is None: return
        self.typed = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        if self.started_at is None and self.typed: self.started_at = time.monotonic(); self.duration_spin.set_sensitive(False); self._apply_privacy_state()
        if self.started_at is not None and time.monotonic() - self.started_at >= self._duration_seconds(): self._finish()
        elif self.started_at is not None and self.privacy_enabled: self._apply_privacy_state()

    def _finish(self) -> None:
        if self.finished or self.finish_pending or self.current_lesson_id is None: return
        self.finish_pending = True
        def finish_idle() -> bool:
            if self.finished: self.finish_pending = False; return GLib.SOURCE_REMOVE
            self.finish_pending = False; self._finish_now(); return GLib.SOURCE_REMOVE
        GLib.idle_add(finish_idle)

    def _finish_now(self) -> None:
        if self.finished or self.current_lesson_id is None: return
        self.finished = True; self.countdown.set_text("00:00"); self.input_view.set_editable(False); self.duration_spin.set_sensitive(True); self._apply_privacy_state()
        elapsed = 0.0 if self.started_at is None else min(time.monotonic() - self.started_at, self._duration_seconds())
        result = self.engine.match_words(self.current_text, self.typed); self._render_target_results(result.matched_target_indices); self._render_input_results(result.correctness)
        self.db.save_result(self.current_lesson_id, elapsed, result.correct, result.wrong)
        self.status.set_text(f"Süre doldu. Doğru: {result.correct}  |  Yanlış: {result.wrong}  |  Toplam: {result.correct + result.wrong}")

    def _render_target_results(self, matched: set[int]) -> None:
        buffer = self.target_view.get_buffer(); buffer.set_text(self.current_text); start, end = buffer.get_start_iter(), buffer.get_end_iter(); buffer.remove_all_tags(start, end)
        base = self._get_tag(buffer, "editor-default", "#111111"); green = self._get_tag(buffer, "correct-target", "#16803c"); base.set_priority(0); green.set_priority(buffer.get_tag_table().get_size() - 1); buffer.apply_tag(base, start, end)
        matches = list(WORD_PATTERN.finditer(self.current_text))
        for index in matched:
            match = matches[index]; buffer.apply_tag(green, buffer.get_iter_at_offset(match.start()), buffer.get_iter_at_offset(match.end()))

    def _render_input_results(self, correctness: list[bool]) -> None:
        buffer = self.input_view.get_buffer(); start, end = buffer.get_start_iter(), buffer.get_end_iter(); buffer.remove_all_tags(start, end)
        base = self._get_tag(buffer, "editor-default", "#111111"); green = self._get_tag(buffer, "correct-input", "#16803c"); red = self._get_tag(buffer, "wrong-input", "#e01b24"); base.set_priority(0); priority = buffer.get_tag_table().get_size() - 1; green.set_priority(priority); red.set_priority(priority); buffer.apply_tag(base, start, end)
        for match, ok in zip(WORD_PATTERN.finditer(self.typed), correctness): buffer.apply_tag(green if ok else red, buffer.get_iter_at_offset(match.start()), buffer.get_iter_at_offset(match.end()))

    def _open_settings(self, _button: Gtk.Button) -> None:
        if self.settings_window is None: self.settings_window = SettingsWindow(self); self.settings_window.connect("close-request", self._settings_closed)
        self.settings_window.present()

    def _settings_closed(self, _window: Adw.Window) -> bool: self.settings_window = None; return False

    def _check_time(self) -> bool:
        if self.finished or self.started_at is None: return True
        remaining = self._duration_seconds() - (time.monotonic() - self.started_at)
        if remaining <= 0: self._finish()
        else: self.countdown.set_text(format_remaining(remaining))
        return True

    def _on_close_request(self, _window: Adw.ApplicationWindow) -> bool:
        if self.tick_id is not None: GLib.source_remove(self.tick_id); self.tick_id = None
        if self.settings_window is not None: self.settings_window.close(); self.settings_window = None
        self.db.close(); return False
