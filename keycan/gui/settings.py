"""Settings surfaces for Keycan's GUI layer."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class SettingsPanel(Gtk.Box):
    """Settings content embedded in the main window sidebar."""

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
        self.append(privacy)

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

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

    def _on_privacy_changed(self, switch: Gtk.Switch, _param) -> None:
        self.parent_window.privacy_enabled = switch.get_active()
        self.parent_window._apply_privacy_state()


class SettingsWindow(Adw.Window):
    """Compatibility wrapper kept while Settings moves into the sidebar."""

    def __init__(self, parent: Gtk.Widget) -> None:
        super().__init__(transient_for=parent, modal=True, title="Ayarlar")
        self.set_default_size(460, 360)
        self.set_size_request(360, 280)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(SettingsPanel(parent))
        self.set_content(toolbar)
