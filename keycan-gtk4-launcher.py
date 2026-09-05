#!/usr/bin/env python3
"""Keycan GTK4 çalışma düzeltmeleri.

Bu dosya, doğrudan gtk_main.py içindeki yazım motorunu değiştirmeden yalnızca
GTK4 görünümündeki sonuç renklendirmesi, gizlilik görünümü ve kaynak listesinin
sunumunu güvenilir hale getirir.
"""

from __future__ import annotations

import re

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

import gtk_main


_original_build_ui = gtk_main.KeycanWindow._build_ui
_original_finish = gtk_main.KeycanWindow._finish
_original_on_input_changed = gtk_main.KeycanWindow._on_input_changed
_original_sources = gtk_main.Database.sources


def _get_or_create_tag(
    buffer: Gtk.TextBuffer, name: str, foreground: str
) -> Gtk.TextTag:
    table = buffer.get_tag_table()
    tag = table.lookup(name)
    if tag is None:
        tag = buffer.create_tag(name, foreground=foreground)
    return tag


def _set_tag_priority(tag: Gtk.TextTag, priority: int) -> None:
    tag.set_priority(max(0, priority))


def _renumber_source_name(name: str, number: int) -> str:
    """Kaynak adının gerçek verisini değiştirmeden yalnızca UI numarasını düzenler."""
    match = re.match(r"^\s*\d+\.\s*(.*)$", name)
    if match:
        return f"{number}. {match.group(1)}"
    return f"{number}. {name}"


def _sources_without_empty_groups(self: gtk_main.Database) -> list[tuple[int, str]]:
    """Dersi olmayan kaynakları listeden çıkar ve kalanları 1'den numarala."""
    rows = _original_sources(self)
    return [
        (source_id, _renumber_source_name(name, index))
        for index, (source_id, name) in enumerate(rows, 1)
        if self.conn.execute(
            "SELECT 1 FROM lessons WHERE source_id = ? LIMIT 1", (source_id,)
        ).fetchone()
    ]


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

    # Gizlilik tag'i dahil bütün eski görünüm tag'lerini temizle.
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
    table = buffer.get_tag_table()
    hidden = _get_or_create_tag(buffer, "privacy-hidden", "#ffffff")

    # Gizlilik tag'i her zaman diğer foreground tag'lerinden daha üstte olsun.
    _set_tag_priority(hidden, table.get_size() - 1)

    # Eski CSS tabanlı gizleme yöntemini tamamen devre dışı bırakıyoruz.
    self.input_view.remove_css_class("keycan-hidden")
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()

    if active:
        buffer.remove_all_tags(start, end)
        buffer.apply_tag(hidden, start, end)
        self.input_view.set_cursor_visible(False)
    else:
        buffer.remove_tag(hidden, start, end)
        self.input_view.set_cursor_visible(
            not self.finished and self.current_lesson_id is not None
        )


def _on_input_changed(self: gtk_main.KeycanWindow, buffer: Gtk.TextBuffer) -> None:
    _original_on_input_changed(self, buffer)
    # Gtk.TextBuffer yeni karakterleri mevcut tag'i her durumda miras almayabilir.
    # Bu nedenle gizlilik açıkken her değişiklikten sonra tüm yazıyı yeniden gizle.
    if not self.finished and self.started_at is not None and self.privacy_enabled:
        _apply_privacy_state(self)


def _build_ui(self: gtk_main.KeycanWindow) -> None:
    _original_build_ui(self)

    # Status, ayarlar ve metin boyutunu aynı CenterBox satırında tut.
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


# Gerçek uygulama yollarına yamaları uygula.
gtk_main.Database.sources = _sources_without_empty_groups
gtk_main.KeycanWindow._build_ui = _build_ui
gtk_main.KeycanWindow._render_target_results = _render_target_results
gtk_main.KeycanWindow._render_input_results = _render_input_results
gtk_main.KeycanWindow._apply_privacy_state = _apply_privacy_state
gtk_main.KeycanWindow._on_input_changed = _on_input_changed
gtk_main.KeycanWindow._finish = _finish


if __name__ == "__main__":
    raise SystemExit(gtk_main.main())
