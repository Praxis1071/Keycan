from __future__ import annotations

import time
from pathlib import Path
from collections import Counter
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from keycan.core.typing_engine import TypingEngine
from keycan.data.database import Database
from keycan.gui.workspace import TypingWorkspace
from keycan.gui.search import SourceSearchDropdown
from keycan.gui.settings2 import SettingsPanel
from keycan.gui.statistics_clean import StatisticsPanel
from keycan.services.i18n import apply_to_widget_tree
from keycan.services.preferences import Preferences
from keycan.utils.text import WORD_PATTERN, format_remaining


CSS = """
headerbar.keycan-header { background: var(--headerbar-bg-color); color: var(--headerbar-fg-color); }
.keycan-content, .keycan-controls, .keycan-bottom { background: var(--window-bg-color); color: var(--window-fg-color); }
.keycan-controls label, .keycan-status { color: var(--window-fg-color); }
.keycan-editor { background: var(--view-bg-color); color: var(--view-fg-color); border: 1px solid var(--border-color); }
.keycan-editor textview, .keycan-editor textview text { background: var(--view-bg-color); color: var(--view-fg-color); }
.keycan-editor textview { padding: 10px; }
.keycan-status { padding: 2px 2px 4px; }
.keycan-countdown { color: var(--window-fg-color); font-weight: 700; font-size: 16px; }
"""


class KeycanWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, database_path: Path) -> None:
        super().__init__(application=app, title="Keycan — On Parmak")
        self.set_default_size(1200, 760)
        self.db = Database(database_path)
        self.engine = TypingEngine()
        self.preferences = Preferences()
        self.current_lesson_id: int | None = None
        self.current_text = ""
        self.typed = ""
        self.finished = False
        self.started_at: float | None = None
        self.updating_input = False
        self.finish_pending = False
        self.tick_id: int | None = None
        self.privacy_enabled = False
        self.backspace_enabled = True
        self.text_size = 16
        self.preferences_popover: Gtk.Popover | None = None
        self._install_css()
        self.apply_theme()
        self._build_ui()
        self._load_sources()
        self.apply_language()
        self.connect("close-request", self._on_close_request)

    def apply_theme(self) -> None:
        manager = Adw.StyleManager.get_default()
        schemes = {
            "system": Adw.ColorScheme.PREFER_LIGHT,
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
        }
        manager.set_color_scheme(schemes[self.preferences.get("theme")])

    def apply_language(self) -> None:
        language = self.preferences.get("language")
        apply_to_widget_tree(self, language)
        # Re-render dynamic pages after a language change so generated
        # statistics/status text is translated too.
        statistics_page = getattr(self, "statistics_page", None)
        if statistics_page is not None:
            statistics_page.refresh()
        apply_to_widget_tree(self, language)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS, -1)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _build_ui(self) -> None:
        toolbar = Adw.ToolbarView()
        toolbar.set_top_bar_style(Adw.ToolbarStyle.FLAT)
        header = Adw.HeaderBar()
        header.add_css_class("keycan-header")
        self.header = header
        toolbar.add_top_bar(header)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.add_css_class("keycan-content")
        root.set_hexpand(True)
        root.set_vexpand(True)
        toolbar.set_content(root)
        self.set_content(toolbar)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        controls.set_hexpand(True)
        controls.set_margin_top(10)
        controls.set_margin_start(0)
        controls.set_margin_end(0)
        controls.set_margin_bottom(8)
        controls.add_css_class("keycan-controls")
        root.append(controls)

        left_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        left_controls.set_hexpand(True)
        left_controls.set_halign(Gtk.Align.FILL)
        left_controls.set_margin_start(12)
        controls.append(left_controls)

        right_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right_controls.set_halign(Gtk.Align.END)
        right_controls.set_margin_start(12)
        right_controls.set_margin_end(12)
        controls.append(right_controls)

        left_controls.append(self._label("Ders grubu:"))
        self.source_dropdown = SourceSearchDropdown()
        self.source_dropdown.on_selected_changed = self._on_source_changed
        self.source_dropdown.set_hexpand(True)
        self.source_dropdown.set_halign(Gtk.Align.FILL)
        left_controls.append(self.source_dropdown)

        left_controls.append(self._label("Metin:"))
        self.lesson_dropdown = Gtk.DropDown()
        self.lesson_dropdown.set_hexpand(True)
        self.lesson_dropdown.set_halign(Gtk.Align.FILL)
        self.lesson_dropdown.connect("notify::selected", self._on_lesson_changed)
        left_controls.append(self.lesson_dropdown)

        right_controls.append(self._label("Süre:"))
        adj = Gtk.Adjustment(value=1, lower=1, upper=180, step_increment=1, page_increment=10)
        self.duration_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        self.duration_spin.set_numeric(True)
        self.duration_spin.set_width_chars(3)
        self.duration_spin.connect("value-changed", self._on_duration_changed)
        right_controls.append(self.duration_spin)
        right_controls.append(self._label("dakika"))

        self.countdown = Gtk.Label(label="01:00")
        self.countdown.add_css_class("keycan-countdown")
        right_controls.append(self.countdown)

        self.restart_button = Gtk.Button(label="Baştan Başla")
        self.restart_button.add_css_class("suggested-action")
        self.restart_button.connect("clicked", self._restart)
        right_controls.append(self.restart_button)

        narrow_breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 900sp")
        )
        narrow_breakpoint.add_setter(controls, "orientation", Gtk.Orientation.VERTICAL)
        narrow_breakpoint.add_setter(controls, "spacing", 6)
        narrow_breakpoint.add_setter(left_controls, "spacing", 4)
        narrow_breakpoint.add_setter(right_controls, "spacing", 4)
        narrow_breakpoint.add_setter(left_controls, "margin-end", 12)
        narrow_breakpoint.add_setter(right_controls, "margin-start", 12)
        narrow_breakpoint.add_setter(right_controls, "halign", Gtk.Align.FILL)
        self.add_breakpoint(narrow_breakpoint)

        compact_breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 620sp")
        )
        compact_breakpoint.add_setter(left_controls, "orientation", Gtk.Orientation.VERTICAL)
        compact_breakpoint.add_setter(left_controls, "halign", Gtk.Align.FILL)
        compact_breakpoint.add_setter(self.source_dropdown, "hexpand", True)
        compact_breakpoint.add_setter(self.lesson_dropdown, "hexpand", True)
        self.add_breakpoint(compact_breakpoint)

        short_breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-height: 650sp")
        )
        short_breakpoint.add_setter(controls, "margin-top", 6)
        short_breakpoint.add_setter(controls, "margin-bottom", 4)
        self.add_breakpoint(short_breakpoint)

        self.workspace = TypingWorkspace(self.text_size)
        workspace_key_controller = Gtk.EventControllerKey()
        workspace_key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        workspace_key_controller.connect("key-pressed", self._on_workspace_key_pressed)
        self.workspace.add_controller(workspace_key_controller)
        self.target_view = self.workspace.target_view
        self.input_view = self.workspace.input_view
        self.status = self.workspace.status
        self.size_spin = self.workspace.size_spin
        self.workspace.preferences_button.connect("clicked", self._toggle_preferences)
        self.input_view.get_buffer().connect("changed", self._on_input_changed)
        self.size_spin.connect("value-changed", self._on_text_size_changed)
        root.append(self.workspace)
        self._build_preferences_popover()

    def _build_preferences_popover(self) -> None:
        popover = Gtk.Popover()
        popover.set_size_request(360, -1)
        popover.set_has_arrow(True)

        group = Adw.PreferencesGroup()
        group.set_title("Tercihler")
        group.set_description("Bu çalışma alanındaki yazma seçenekleri")
        group.set_margin_top(8)
        group.set_margin_bottom(8)
        group.set_margin_start(8)
        group.set_margin_end(8)

        privacy = Adw.SwitchRow()
        privacy.set_title("Yazım metnini karart")
        privacy.set_subtitle("Yazarken girdiğin metni gizler")
        privacy.set_active(self.privacy_enabled)
        privacy.connect("notify::active", self._on_privacy_changed)
        group.add(privacy)
        self.privacy_switch = privacy

        backspace = Adw.SwitchRow()
        backspace.set_title("Geri tuşunu devre dışı bırak")
        backspace.set_subtitle("Yazarken önceki karakteri silmeyi engeller")
        backspace.set_active(not self.backspace_enabled)
        backspace.connect("notify::active", self._on_backspace_changed)
        group.add(backspace)
        self.backspace_switch = backspace

        popover.set_child(group)
        self.preferences_popover = popover

    def _toggle_preferences(self, _button: Gtk.Button) -> None:
        if self.preferences_popover is None:
            return
        if self.preferences_popover.get_parent() is None:
            self.preferences_popover.set_parent(self.workspace.preferences_button)
        if self.preferences_popover.is_visible():
            self.preferences_popover.popdown()
        else:
            self.preferences_popover.popup()

    def _on_privacy_changed(self, row: Adw.SwitchRow, _param) -> None:
        self.privacy_enabled = row.get_active()
        self._apply_privacy_state()

    def _on_backspace_changed(self, row: Adw.SwitchRow, _param) -> None:
        self.backspace_enabled = not row.get_active()
        self.workspace.set_backspace_enabled(self.backspace_enabled)

    @staticmethod
    def _label(text: str) -> Gtk.Label:
        label = Gtk.Label(label=text)
        label.set_xalign(0)
        return label

    def _on_text_size_changed(self, spin: Gtk.SpinButton) -> None:
        self.text_size = int(spin.get_value())
        self.workspace.set_text_size(self.text_size)

    def _load_sources(self) -> None:
        sources = self.db.sources()
        self.source_ids = [i for i, _ in sources]
        self.source_dropdown.set_model(Gtk.StringList.new([n for _, n in sources]))
        if sources:
            self.source_dropdown.set_selected(0)

    def _load_lessons(self, source_id: int) -> None:
        lessons = self.db.lessons(source_id)
        self.lesson_ids = [i for i, _ in lessons]
        self.lesson_dropdown.set_model(Gtk.StringList.new([n for _, n in lessons]))
        if lessons:
            self.lesson_dropdown.set_selected(0)
        else:
            self.current_lesson_id = None
            self.current_text = ""
            self._restart()

    def _on_source_changed(self, _dropdown: Gtk.DropDown, _param) -> None:
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids):
            self._load_lessons(self.source_ids[index])

    def _on_lesson_changed(self, _dropdown: Gtk.DropDown, _param) -> None:
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
        self.finish_pending = False
        self.started_at = None
        self.duration_spin.set_sensitive(True)
        self.countdown.set_text(format_remaining(self._duration_seconds()))
        self.updating_input = True
        self.workspace.set_input_text("")
        self.updating_input = False
        self.workspace.set_target_text(self.current_text)
        self.input_view.set_editable(self.current_lesson_id is not None)
        self.workspace.set_backspace_enabled(self.backspace_enabled)
        self._apply_privacy_state()
        if self.current_lesson_id:
            self.status.set_text("Yazmaya başlayınca geri sayım çalışır.")
            self.input_view.grab_focus()
        else:
            self.status.set_text("Bir ders ve metin seçin.")
        if self.tick_id is None:
            self.tick_id = GLib.timeout_add(100, self._check_time)

    def _set_input_text(self, text: str) -> None:
        self.updating_input = True
        self.workspace.set_input_text(text)
        self.updating_input = False

    def _set_target_text(self, text: str) -> None:
        self.workspace.set_target_text(text)

    def _editor_foreground(self) -> str:
        return "#f2f2f2" if Adw.StyleManager.get_default().get_dark() else "#111111"

    @staticmethod
    def _get_tag(buffer: Gtk.TextBuffer, name: str, foreground: str) -> Gtk.TextTag:
        table = buffer.get_tag_table()
        tag = table.lookup(name)
        if tag is None:
            tag = buffer.create_tag(name, foreground=foreground)
        return tag

    def _apply_privacy_state(self) -> None:
        active = self.privacy_enabled and self.started_at is not None and not self.finished
        buffer = self.input_view.get_buffer()
        hidden = self._get_tag(buffer, "privacy-hidden", self._editor_foreground())
        hidden.set_priority(max(0, buffer.get_tag_table().get_size() - 1))
        self.input_view.remove_css_class("keycan-hidden")
        start, end = buffer.get_start_iter(), buffer.get_end_iter()
        if active:
            buffer.remove_all_tags(start, end)
            buffer.apply_tag(hidden, start, end)
            self.input_view.set_cursor_visible(False)
        else:
            buffer.remove_tag(hidden, start, end)
            self.input_view.set_cursor_visible(not self.finished and self.current_lesson_id is not None)

    def _start_session(self) -> None:
        if self.started_at is not None or self.finished or self.current_lesson_id is None:
            return
        self.started_at = time.monotonic()
        self.duration_spin.set_sensitive(False)
        self.status.set_text("Ders başladı. Yazmaya devam et.")
        self._apply_privacy_state()

    def _on_workspace_key_pressed(self, _controller, keyval, _keycode, state) -> bool:
        if self.current_lesson_id is None or self.finished or self.started_at is not None:
            return False
        if state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.ALT_MASK | Gdk.ModifierType.META_MASK):
            return False
        unicode_value = Gdk.keyval_to_unicode(keyval)
        if not unicode_value:
            return False
        character = chr(unicode_value)
        if not character.isalpha():
            return False

        self._start_session()
        if self.input_view.has_focus():
            return False

        self.input_view.grab_focus()
        buffer = self.input_view.get_buffer()
        buffer.insert_at_cursor(character)
        return True

    def _on_input_changed(self, buffer: Gtk.TextBuffer) -> None:
        if self.updating_input or self.finished or self.current_lesson_id is None:
            return
        self.typed = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        if self.started_at is None and self.typed:
            self._start_session()
        if self.started_at is not None and time.monotonic() - self.started_at >= self._duration_seconds():
            self._finish()
        elif self.started_at is not None and self.privacy_enabled:
            self._apply_privacy_state()

    def _finish(self) -> None:
        if self.finished or self.finish_pending or self.current_lesson_id is None:
            return
        self.finish_pending = True

        def finish_idle() -> bool:
            if self.finished:
                self.finish_pending = False
                return GLib.SOURCE_REMOVE
            self.finish_pending = False
            self._finish_now()
            return GLib.SOURCE_REMOVE

        GLib.idle_add(finish_idle)

    def _finish_now(self) -> None:
        if self.finished or self.current_lesson_id is None:
            return
        self.finished = True
        self.countdown.set_text("00:00")
        self.input_view.set_editable(False)
        self.duration_spin.set_sensitive(True)
        self._apply_privacy_state()
        elapsed = 0.0 if self.started_at is None else min(time.monotonic() - self.started_at, self._duration_seconds())
        result = self.engine.match_words(self.current_text, self.typed)
        self._render_target_results(result.matched_target_indices)
        self._render_input_results(result.correctness)

        target_word_count = len(WORD_PATTERN.findall(self.current_text))
        typed_word_count = len(WORD_PATTERN.findall(self.typed))
        total_characters = len(self.typed)
        character_correctness = self.engine.character_correctness(self.current_text, self.typed)
        correct_characters = sum(character_correctness)
        wrong_characters = total_characters - correct_characters
        minutes = elapsed / 60.0 if elapsed > 0 else 0.0
        words_per_minute = typed_word_count / minutes if minutes else 0.0
        characters_per_minute = total_characters / minutes if minutes else 0.0
        accuracy_percent = result.correct / typed_word_count * 100.0 if typed_word_count else 0.0
        wrong_letters = Counter()
        for index, typed_char in enumerate(self.typed):
            if index < len(self.current_text) and not character_correctness[index]:
                expected = self.current_text[index]
                if expected.isalpha():
                    wrong_letters[expected.lower()] += 1
                elif typed_char.isalpha():
                    wrong_letters[typed_char.lower()] += 1
        if len(self.typed) > len(self.current_text):
            for typed_char in self.typed[len(self.current_text):]:
                if typed_char.isalpha():
                    wrong_letters[typed_char.lower()] += 1

        self.db.save_result(
            self.current_lesson_id,
            elapsed,
            result.correct,
            result.wrong,
            target_word_count=target_word_count,
            typed_word_count=typed_word_count,
            total_characters=total_characters,
            correct_characters=correct_characters,
            wrong_characters=wrong_characters,
            words_per_minute=words_per_minute,
            characters_per_minute=characters_per_minute,
            accuracy_percent=accuracy_percent,
            wrong_letter_counts=dict(wrong_letters),
        )
        self.status.set_text(
            f"Süre doldu. Doğru: {result.correct}  |  Yanlış: {result.wrong}  |  Toplam: {typed_word_count}"
        )

    def _render_target_results(self, matched: set[int]) -> None:
        buffer = self.target_view.get_buffer()
        buffer.set_text(self.current_text)
        start, end = buffer.get_start_iter(), buffer.get_end_iter()
        buffer.remove_all_tags(start, end)
        base = self._get_tag(buffer, "editor-default", self._editor_foreground())
        green = self._get_tag(buffer, "correct-target", "#16803c")
        base.set_priority(0)
        green.set_priority(buffer.get_tag_table().get_size() - 1)
        buffer.apply_tag(base, start, end)
        matches = list(WORD_PATTERN.finditer(self.current_text))
        for index in matched:
            match = matches[index]
            buffer.apply_tag(green, buffer.get_iter_at_offset(match.start()), buffer.get_iter_at_offset(match.end()))

    def _render_input_results(self, correctness: list[bool]) -> None:
        buffer = self.input_view.get_buffer()
        start, end = buffer.get_start_iter(), buffer.get_end_iter()
        buffer.remove_all_tags(start, end)
        base = self._get_tag(buffer, "editor-default", "#111111")
        green = self._get_tag(buffer, "correct-input", "#16803c")
        red = self._get_tag(buffer, "wrong-input", "#e01b24")
        base.set_priority(0)
        green.set_priority(buffer.get_tag_table().get_size() - 1)
        red.set_priority(buffer.get_tag_table().get_size() - 1)
        buffer.apply_tag(base, start, end)
        for match, ok in zip(WORD_PATTERN.finditer(self.typed), correctness):
            buffer.apply_tag(green if ok else red, buffer.get_iter_at_offset(match.start()), buffer.get_iter_at_offset(match.end()))

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
        if self.preferences_popover is not None:
            self.preferences_popover.popdown()
            self.preferences_popover.unparent()
            self.preferences_popover = None
        self.db.close()
        return False


class ConfiguredKeycanWindow(KeycanWindow):
    """Production application shell composed from the base typing window."""

    def __init__(self, app: Adw.Application, database_path: Path):
        super().__init__(app, database_path)
        self.maximize()
        self.text_size = 22
        self.size_spin.set_value(22)
        self.workspace.set_text_size(self.text_size)

    def _build_ui(self) -> None:
        super()._build_ui()
        self._install_sidebar_navigation()
        compact_height = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-height: 650sp"))
        compact_height.add_setter(self.workspace.editors, "position", 280)
        self.add_breakpoint(compact_height)
        short_height = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-height: 520sp"))
        short_height.add_setter(self.workspace.editors, "position", 210)
        short_height.add_setter(self.workspace.bottom, "height-request", 30)
        self.add_breakpoint(short_height)

    def _install_sidebar_navigation(self) -> None:
        toolbar = self.get_content()
        if not isinstance(toolbar, Adw.ToolbarView):
            return
        root = toolbar.get_content()
        if not isinstance(root, Gtk.Box):
            return
        split = Adw.OverlaySplitView()
        split.set_collapsed(True)
        split.set_sidebar_position(Gtk.PackType.START)
        split.set_min_sidebar_width(260)
        split.set_max_sidebar_width(340)
        split.set_sidebar_width_fraction(0.25)
        split.set_show_sidebar(False)
        split.set_enable_show_gesture(True)
        split.set_enable_hide_gesture(True)
        nav = Gtk.ListBox()
        nav.add_css_class("navigation-sidebar")
        nav.set_selection_mode(Gtk.SelectionMode.SINGLE)
        nav.set_activate_on_single_click(True)
        nav.set_show_separators(False)
        nav.set_margin_top(12); nav.set_margin_start(12); nav.set_margin_end(12); nav.set_margin_bottom(12)
        nav.set_vexpand(True)
        rows = [
            self._make_navigation_row("Çalışma Alanı", "input-keyboard-symbolic", "workspace"),
            self._make_navigation_row("İstatistikler", "utilities-system-monitor-symbolic", "statistics"),
            self._make_navigation_row("Ayarlar", "emblem-system-symbolic", "settings"),
        ]
        for row in rows:
            nav.append(row)
        nav.select_row(rows[0])
        toolbar.set_content(None)
        stack = Gtk.Stack(); stack.set_hexpand(True); stack.set_vexpand(True)
        stack.add_named(root, "workspace")
        stats = StatisticsPanel(self.db); stats.set_hexpand(True); stats.set_vexpand(True)
        stack.add_named(stats, "statistics")
        settings = SettingsPanel(self, on_content_changed=self._load_sources, on_statistics_changed=stats.refresh)
        settings.set_hexpand(True); settings.set_vexpand(True)
        settings_scroll = Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_scroll.set_hexpand(True); settings_scroll.set_vexpand(True)
        settings_scroll.set_child(settings)
        stack.add_named(settings_scroll, "settings")
        stack.set_visible_child_name("workspace")
        def activated(_list, row):
            name = row.get_name()
            if name not in {"workspace", "statistics", "settings"}:
                return
            stack.set_visible_child_name(name)
            if name == "statistics":
                stats.refresh()
            split.set_show_sidebar(False)
        nav.connect("row-activated", activated)
        split.set_sidebar(nav); split.set_content(stack); toolbar.set_content(split)
        self.sidebar_view = split; self.navigation_list = nav; self.content_stack = stack; self.statistics_page = stats
        toggle = Gtk.ToggleButton(); toggle.set_icon_name("sidebar-show-symbolic")
        toggle.set_tooltip_text("Yan paneli aç/kapat")
        toggle.connect("toggled", lambda button: split.set_show_sidebar(button.get_active()))
        split.connect("notify::show-sidebar", lambda view, _param: toggle.set_active(view.get_show_sidebar()))
        self.header.pack_start(toggle); self.sidebar_toggle_button = toggle

    @staticmethod
    def _make_navigation_row(title: str, icon_name: str, page_name: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow(); row.set_name(page_name); row.set_activatable(True); row.set_selectable(True)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon = Gtk.Image.new_from_icon_name(icon_name); icon.set_pixel_size(18); box.append(icon)
        label = Gtk.Label(label=title); label.set_xalign(0); label.set_hexpand(True); box.append(label)
        row.set_child(box); return row

    def _load_sources(self) -> None:
        sources = self.db.sources()
        self.source_ids = [source_id for source_id, _name in sources]
        self.source_dropdown.set_model(Gtk.StringList.new([name for _source_id, name in sources]))
        if sources:
            self.source_dropdown.set_selected(0)
            return
        self.lesson_ids = []
        self.lesson_dropdown.set_model(Gtk.StringList.new([]))
        self.current_lesson_id = None; self.current_text = ""; self._restart()

    def _on_source_changed(self, _dropdown, _param) -> None:
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids):
            self._load_lessons(self.source_ids[index])


# Export the fully composed window so app.py needs no monkey-patching from main.py.
KeycanWindow = ConfiguredKeycanWindow
