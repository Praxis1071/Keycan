"""Typing workspace UI for Keycan.

This module owns the typing surface and result-display widgets only. Application
state, typing logic, privacy state, and persistence remain in the main window.

The practice views deliberately disable clipboard editing actions so a session
cannot be completed by pasting text. Normal keyboard input and backspace remain
available in the input view.
"""

from __future__ import annotations

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk


class PracticeTextView(Gtk.TextView):
    """Text view with the clipboard/editing loopholes closed for practice."""

    _BLOCKED_ACTIONS = (
        "clipboard.copy",
        "clipboard.cut",
        "clipboard.paste",
    )

    def __init__(self, editable: bool, monospace: bool) -> None:
        super().__init__()
        self.set_editable(editable)
        self.set_cursor_visible(editable)
        self.set_monospace(monospace)
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_left_margin(8)
        self.set_right_margin(8)
        self.set_top_margin(8)
        self.set_bottom_margin(8)
        self.set_extra_menu(None)

        # GTK4 TextView exposes clipboard operations as built-in widget
        # actions. Disabling them covers keyboard shortcuts and the matching
        # context-menu commands without affecting ordinary typing.
        for action_name in self._BLOCKED_ACTIONS:
            self.action_set_enabled(action_name, False)

        # Undo/redo must not become an alternate way to alter a practice
        # result. Backspace itself remains enabled for normal typing.
        self.action_set_enabled("text.undo", False)
        self.action_set_enabled("text.redo", False)
        self.get_buffer().set_enable_undo(False)

        # GTK can use PRIMARY selection on middle-click. Capture the middle
        # button before TextView sees it so it cannot become a paste shortcut.
        self._middle_click_guard = Gtk.GestureClick()
        self._middle_click_guard.set_button(2)
        self._middle_click_guard.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self._middle_click_guard.connect("pressed", self._block_middle_click)
        self.add_controller(self._middle_click_guard)

    @staticmethod
    def _block_middle_click(gesture: Gtk.GestureClick, *_args) -> None:
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)


class TypingWorkspace(Gtk.Box):
    """Reusable typing workspace surface."""

    def __init__(self, text_size: int = 16) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.text_size = text_size
        self.text_providers: dict[Gtk.TextView, Gtk.CssProvider] = {}

        editors = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        editors.set_vexpand(True)
        editors.set_wide_handle(True)
        editors.set_margin_start(12)
        editors.set_margin_end(12)
        editors.set_margin_bottom(4)
        self.append(editors)

        self.target_view = self._make_text_view(False, False)
        editors.set_start_child(self._wrap_editor(self.target_view))

        self.input_view = self._make_text_view(True, True)
        editors.set_end_child(self._wrap_editor(self.input_view))
        editors.set_position(470)

        bottom = Gtk.CenterBox()
        bottom.set_margin_start(0)
        bottom.set_margin_end(0)
        bottom.set_size_request(-1, 34)
        bottom.add_css_class("keycan-bottom")
        self.append(bottom)

        self.status = Gtk.Label(label="Bir ders ve metin seçin.")
        self.status.set_xalign(0)
        self.status.set_margin_start(12)
        self.status.add_css_class("keycan-status")
        bottom.set_start_widget(self.status)

        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        size_box.set_halign(Gtk.Align.END)
        size_box.set_margin_end(12)
        size_box.append(Gtk.Label(label="Metin boyutu:"))
        size_adj = Gtk.Adjustment(
            value=self.text_size,
            lower=12,
            upper=30,
            step_increment=1,
            page_increment=2,
        )
        self.size_spin = Gtk.SpinButton(adjustment=size_adj, climb_rate=1, digits=0)
        self.size_spin.set_numeric(True)
        self.size_spin.set_width_chars(3)
        self.size_spin.set_tooltip_text("Ders ve yazım metni boyutu")
        size_box.append(self.size_spin)
        bottom.set_end_widget(size_box)

    def _make_text_view(self, editable: bool, monospace: bool) -> PracticeTextView:
        view = PracticeTextView(editable, monospace)
        self._apply_text_size(view)
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

    def _apply_text_size(self, view: Gtk.TextView | None = None) -> None:
        views = [view] if view is not None else [self.target_view, self.input_view]
        for text_view in views:
            old = self.text_providers.get(text_view)
            if old is not None:
                text_view.get_style_context().remove_provider(old)
            provider = Gtk.CssProvider()
            provider.load_from_data(f"textview {{ font-size: {self.text_size}px; }}", -1)
            text_view.get_style_context().add_provider(
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            self.text_providers[text_view] = provider

    def set_text_size(self, size: int) -> None:
        self.text_size = size
        self._apply_text_size()

    def set_target_text(self, text: str) -> None:
        self.target_view.get_buffer().set_text(text)

    def set_input_text(self, text: str) -> None:
        self.input_view.get_buffer().set_text(text)

    def get_input_text(self) -> str:
        buffer = self.input_view.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
