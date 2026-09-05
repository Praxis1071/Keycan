#!/usr/bin/env python3
"""Keycan GTK4 başlatıcısı.

GTK4 TextView sonuçlarının renklerini ve alt kontrol satırının yerleşimini
uygulama başlatılırken güvenilir biçimde düzeltir. Yazma motoruna ve veriye
dokunmaz.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

import gtk_main


_original_build_ui = gtk_main.KeycanWindow._build_ui
_original_finish = gtk_main.KeycanWindow._finish


def _get_or_create_tag(buffer: Gtk.TextBuffer, name: str, foreground: str) -> Gtk.TextTag:
    table = buffer.get_tag_table()
    tag = table.lookup(name)
    if tag is None:
        tag = buffer.create_tag(name, foreground=foreground)
    return tag


def _set_tag_priority(tag: Gtk.TextTag, priority: int) -> None:
    try:
        tag.set_priority(priority)
    except (TypeError, ValueError):
        pass


def _render_target_results(self: gtk_main.KeycanWindow, matched: set[int]) -> None:
    buffer = self.target_view.get_buffer()
    buffer.set_text(self.current_text)

    start = buffer.get_start_iter()
    end = buffer.get_end_iter()
    buffer.remove_all_tags(start, end)

    base = _get_or_create_tag(buffer, "editor-default", "#111111")
    green = _get_or_create_tag(buffer, "correct-target", "#16803c")
    _set_tag_priority(base, 0)
    _set_tag_priority(green, buffer.get_tag_table().get_size() - 1)
    buffer.apply_tag(base, start, end)

    target_matches = list(gtk_main.WORD_PATTERN.finditer(self.current_text))
    for index in matched:
        match = target_matches[index]
        match_start = buffer.get_iter_at_offset(match.start())
        match_end = buffer.get_iter_at_offset(match.end())
        buffer.apply_tag(green, match_start, match_end)


def _render_input_results(self: gtk_main.KeycanWindow, correctness: list[bool]) -> None:
    buffer = self.input_view.get_buffer()
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()

    # Sonuç ekranına girerken gizlilik ve önceki sonuç tag'lerinin tamamını temizle.
    buffer.remove_all_tags(start, end)

    base = _get_or_create_tag(buffer, "editor-default", "#111111")
    green = _get_or_create_tag(buffer, "correct-input", "#16803c")
    red = _get_or_create_tag(buffer, "wrong-input", "#e01b24")
    _set_tag_priority(base, 0)
    result_priority = buffer.get_tag_table().get_size() - 1
    _set_tag_priority(green, result_priority)
    _set_tag_priority(red, result_priority)
    buffer.apply_tag(base, start, end)

    matches = list(gtk_main.WORD_PATTERN.finditer(self.typed))
    for match, is_correct in zip(matches, correctness):
        match_start = buffer.get_iter_at_offset(match.start())
        match_end = buffer.get_iter_at_offset(match.end())
        buffer.apply_tag(green if is_correct else red, match_start, match_end)


def _apply_privacy_state(self: gtk_main.KeycanWindow) -> None:
    active = self.privacy_enabled and self.started_at is not None and not self.finished
    buffer = self.input_view.get_buffer()
    hidden = _get_or_create_tag(buffer, "privacy-hidden", "#ffffff")
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()

    self.input_view.remove_css_class("keycan-hidden")
    if active:
        buffer.apply_tag(hidden, start, end)
        self.input_view.set_cursor_visible(False)
    else:
        buffer.remove_tag(hidden, start, end)
        self.input_view.set_cursor_visible(
            not self.finished and self.current_lesson_id is not None
        )


def _build_ui(self: gtk_main.KeycanWindow) -> None:
    _original_build_ui(self)

    # Státuszu CenterBox'ın sol tarafına alıyoruz; sonuç, ayarlar ve metin
    # boyutu artık aynı yatay satırda hizalanır ve ayrı siyah satır kalmaz.
    toolbar = self.get_content()
    root = toolbar.get_content()
    bottom = None
    child = root.get_first_child()
    while child is not None:
        if isinstance(child, Gtk.CenterBox):
            bottom = child
            break
        child = child.get_next_sibling()

    if bottom is not None and self.status.get_parent() is root:
        self.status.unparent()
        self.status.set_margin_start(0)
        self.status.set_margin_end(0)
        self.status.set_xalign(0)
        bottom.set_start_widget(self.status)


def _finish(self: gtk_main.KeycanWindow) -> None:
    if self.finished or getattr(self, "finish_pending", False) or self.current_lesson_id is None:
        return
    self.finish_pending = True

    def finish_idle() -> bool:
        if self.finished:
            self.finish_pending = False
            return GLib.SOURCE_REMOVE
        self.finish_pending = False
        _original_finish(self)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(finish_idle)


# gtk_main.py içindeki gerçek çalışma yollarını uygulama başlatılmadan önce değiştiriyoruz.
gtk_main.KeycanWindow._build_ui = _build_ui
gtk_main.KeycanWindow._render_target_results = _render_target_results
gtk_main.KeycanWindow._render_input_results = _render_input_results
gtk_main.KeycanWindow._apply_privacy_state = _apply_privacy_state
gtk_main.KeycanWindow._finish = _finish


if __name__ == "__main__":
    raise SystemExit(gtk_main.main())
