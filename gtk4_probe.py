#!/usr/bin/env python3
"""Minimal GTK4/libadwaita environment probe for Keycan Stage 5."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


class ProbeWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Keycan GTK4 Probe")
        self.set_default_size(480, 240)

        label = Gtk.Label(label="GTK4 + libadwaita altyapısı hazır.")
        label.set_margin_top(32)
        label.set_margin_bottom(32)
        label.set_margin_start(32)
        label.set_margin_end(32)
        self.set_content(label)


class ProbeApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.keycan.KeycanProbe")

    def do_activate(self):
        ProbeWindow(self).present()


if __name__ == "__main__":
    ProbeApplication().run()
