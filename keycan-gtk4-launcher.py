#!/usr/bin/env python3
"""Keycan GTK4 gizlilik sonucu düzeltmesi.

Gizlilik modunda metni CSS ile gizlemek yerine Gtk.TextTag kullanır.
Süre bitiminde gizlilik tag'i kaldırılır ve mevcut sonuç renkleri uygulanır.
Bitiş işlemi de GTK ana döngüsünün bir sonraki turuna ertelenir.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib

import gtk_main

_original_on_input_changed = gtk_main.KeycanWindow._on_input_changed
_original_finish = gtk_main.KeycanWindow._finish


def _apply_privacy_state(self: gtk_main.KeycanWindow) -> None:
    active = self.privacy_enabled and self.started_at is not None and not self.finished
    buffer = self.input_view.get_buffer()
    tag_table = buffer.get_tag_table()
    hidden_tag = tag_table.lookup("privacy-hidden")
    if hidden_tag is None:
        hidden_tag = buffer.create_tag("privacy-hidden", foreground="#ffffff")

    self.input_view.remove_css_class("keycan-hidden")
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()
    if active:
        buffer.apply_tag(hidden_tag, start, end)
        self.input_view.set_cursor_visible(False)
    else:
        buffer.remove_tag(hidden_tag, start, end)
        self.input_view.set_cursor_visible(
            not self.finished and self.current_lesson_id is not None
        )


def _on_input_changed(self: gtk_main.KeycanWindow, buffer) -> None:
    _original_on_input_changed(self, buffer)
    if not self.finished and self.started_at is not None and self.privacy_enabled:
        _apply_privacy_state(self)


def _finish(self: gtk_main.KeycanWindow) -> None:
    if self.finished or getattr(self, "finish_pending", False) or self.current_lesson_id is None:
        return
    self.finish_pending = True

    def finish_idle() -> bool:
        self.finish_pending = False
        _original_finish(self)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(finish_idle)


gtk_main.KeycanWindow._apply_privacy_state = _apply_privacy_state
gtk_main.KeycanWindow._on_input_changed = _on_input_changed
gtk_main.KeycanWindow._finish = _finish

if __name__ == "__main__":
    raise SystemExit(gtk_main.main())
