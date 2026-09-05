#!/usr/bin/env python3
"""Keycan GTK4 başlatıcısı.

Süre bitişini ana GTK döngüsünün bir sonraki turuna erteleyerek,
"Yazım metnini karart" açıkken sonuç TextTag renklerinin güvenilir
şekilde uygulanmasını sağlar. Yazım motoruna ve veritabanına dokunmaz.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib

import gtk_main

_original_finish = gtk_main.KeycanWindow._finish


def _deferred_finish(self: gtk_main.KeycanWindow) -> None:
    if self.finished or getattr(self, "finish_pending", False) or self.current_lesson_id is None:
        return
    self.finish_pending = True

    def finish_idle() -> bool:
        self.finish_pending = False
        _original_finish(self)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(finish_idle)


gtk_main.KeycanWindow._finish = _deferred_finish


if __name__ == "__main__":
    raise SystemExit(gtk_main.main())
