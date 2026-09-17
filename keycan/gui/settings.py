"""Application settings surface for Keycan."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class SettingsPanel(Gtk.Box):
    """Application-level settings embedded in the sidebar."""

    def __init__(self, parent: Gtk.Widget) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.parent_window = parent
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)

        title = Gtk.Label(label="Ayarlar")
        title.set_xalign(0)
        title.add_css_class("title-2")
        self.append(title)

        about_title = Gtk.Label(label="Hakkında")
        about_title.set_xalign(0)
        about_title.add_css_class("title-3")
        self.append(about_title)

        about = Gtk.Label(
            label="Keycan, Linux üzerinde on parmak yazma pratiği yapmayı kolaylaştırmak için geliştirilmiş, sade ve açık kaynaklı bir projedir.\n\nGeliştirici: Praxis1071"
        )
        about.set_xalign(0)
        about.set_wrap(True)
        self.append(about)

        github = Gtk.LinkButton(
            uri="https://github.com/Praxis1071",
            label="GitHub profili: github.com/Praxis1071",
        )
        github.set_halign(Gtk.Align.START)
        self.append(github)


class SettingsWindow(Adw.Window):
    """Compatibility wrapper for older callers."""

    def __init__(self, parent: Gtk.Widget) -> None:
        super().__init__(transient_for=parent, modal=True, title="Ayarlar")
        self.set_default_size(460, 300)
        self.set_size_request(360, 240)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(SettingsPanel(parent))
        self.set_content(toolbar)
