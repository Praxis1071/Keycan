"""Settings window for Keycan's GUI layer."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class SettingsWindow(Adw.Window):
    """Settings surface owned by the GUI layer.

    The parent window remains responsible for application state; this widget
    only presents controls and forwards changes through its parent callbacks.
    """

    def __init__(self, parent: "Gtk.Widget") -> None:
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
        title.set_xalign(0)
        title.add_css_class("title-3")
        about.append(title)

        developer = Gtk.Label(label="Geliştirici: Praxis1071")
        developer.set_xalign(0)
        about.append(developer)

        github = Gtk.LinkButton(
            uri="https://github.com/Praxis1071",
            label="GitHub profili: github.com/Praxis1071",
        )
        github.set_halign(Gtk.Align.START)
        about.append(github)
        content.append(about)
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        privacy = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        label = Gtk.Label(label="Yazım metnini karart")
        label.set_xalign(0)
        label.set_hexpand(True)
        details.append(label)

        description = Gtk.Label(
            label="Yazarken kendi yazdığın metni gizler; süre bitince sonuçları gösterir."
        )
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        details.append(description)
        privacy.append(details)

        self.privacy_switch = Gtk.Switch()
        self.privacy_switch.set_valign(Gtk.Align.CENTER)
        self.privacy_switch.set_active(parent.privacy_enabled)
        self.privacy_switch.connect("notify::active", self._on_privacy_changed)
        privacy.append(self.privacy_switch)
        content.append(privacy)

    def _on_privacy_changed(self, switch: Gtk.Switch, _param) -> None:
        self.parent_window.privacy_enabled = switch.get_active()
        self.parent_window._apply_privacy_state()
