"""Presentation construction for the main Keycan window."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from keycan.gui.search import SourceSearchDropdown
from keycan.gui.workspace import TypingWorkspace


CSS = """
headerbar.keycan-header { background: @headerbar_bg_color; color: @headerbar_fg_color; }
.keycan-content, .keycan-controls, .keycan-bottom { background: @window_bg_color; color: @window_fg_color; }
.keycan-controls label, .keycan-status { color: @window_fg_color; }
.keycan-editor { background: @view_bg_color; color: @view_fg_color; border: 1px solid @borders; }
.keycan-editor textview, .keycan-editor textview text { background: @view_bg_color; color: @view_fg_color; }
.keycan-editor textview { padding: 10px; }
.keycan-status { padding: 2px 2px 4px; }
.keycan-countdown { color: @window_fg_color; font-weight: 700; font-size: 16px; }
"""


class WindowLayoutMixin:
    """Build the main typing workspace and its preference controls."""

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

            input_key_controller = Gtk.EventControllerKey()
            input_key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            input_key_controller.connect("key-pressed", self._on_input_key_pressed)
            self.input_view.add_controller(input_key_controller)
            self.status = self.workspace.status
            self.workspace.retry_save_button.connect("clicked", self._retry_save_results)
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


__all__ = ["WindowLayoutMixin"]
