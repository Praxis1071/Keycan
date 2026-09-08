#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

import keycan.app as keycan_app
import keycan.window as keycan_window
from keycan.app import main


class ConfiguredKeycanWindow(keycan_window.KeycanWindow):
    def __init__(self, app: Adw.Application, database_path):
        super().__init__(app, database_path)

        # Keycan starts maximized so the main workspace fills the screen.
        self.maximize()

        # 22 is the default text size; the existing size control remains unchanged.
        self.text_size = 22
        self.size_spin.set_value(22)
        self._apply_text_size()

        # Use GTK's native DropDown search for the long source list.
        # GTK's string filter is case-insensitive by default and matches substrings.
        self.source_dropdown.set_enable_search(True)


class SettingsWindow(Adw.Window):
    def __init__(self, parent: "keycan_window.KeycanWindow") -> None:
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

        stack = Gtk.Stack()
        stack.set_vexpand(True)
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.CENTER)
        content.append(switcher)
        content.append(stack)

        general = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        general.set_valign(Gtk.Align.START)
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        label = Gtk.Label(label="Yazım metnini karart")
        label.set_xalign(0)
        label.set_hexpand(True)
        details.append(label)
        description = Gtk.Label(label="Yazarken kendi yazdığın metni gizler; süre bitince sonuçları gösterir.")
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        details.append(description)
        general.append(details)
        self.privacy_switch = Gtk.Switch()
        self.privacy_switch.set_valign(Gtk.Align.CENTER)
        self.privacy_switch.set_active(parent.privacy_enabled)
        self.privacy_switch.connect("notify::active", self._on_privacy_changed)
        general.append(self.privacy_switch)
        stack.add_titled(general, "general", "Genel")

        about = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        about.set_valign(Gtk.Align.START)

        title = Gtk.Label(label="Keycan Hakkında")
        title.set_xalign(0)
        title.add_css_class("title-3")
        about.append(title)

        description = Gtk.Label(
            label="Keycan, Linux üzerinde on parmak yazma pratiği yapmayı kolaylaştırmak için geliştirilmiş, sade ve açık kaynaklı bir projedir."
        )
        description.set_xalign(0)
        description.set_wrap(True)
        about.append(description)

        developer = Gtk.Label(label="Geliştirici: Praxis1071")
        developer.set_xalign(0)
        about.append(developer)

        github = Gtk.LinkButton(uri="https://github.com/Praxis1071", label="GitHub profili: github.com/Praxis1071")
        github.set_halign(Gtk.Align.START)
        about.append(github)

        youtube = Gtk.LinkButton(uri="https://www.youtube.com/@Praxis1071", label="YouTube kanalı: youtube.com/@Praxis1071")
        youtube.set_halign(Gtk.Align.START)
        about.append(youtube)

        website = Gtk.LinkButton(uri="https://ozcanbilgisayarkursu.com", label="Özcan Bilgisayar Kursu: ozcanbilgisayarkursu.com")
        website.set_halign(Gtk.Align.START)
        about.append(website)

        thanks = Gtk.Label(
            label="Keycan projesine verdiği destek ve katkıları için Malik Özcan Hocam'a teşekkür ederim."
        )
        thanks.set_xalign(0)
        thanks.set_wrap(True)
        about.append(thanks)

        stack.add_titled(about, "about", "Hakkında")
        stack.set_visible_child_name("general")

    def _on_privacy_changed(self, switch: Gtk.Switch, _param) -> None:
        self.parent_window.privacy_enabled = switch.get_active()
        self.parent_window._apply_privacy_state()


keycan_window.SettingsWindow = SettingsWindow
keycan_window.KeycanWindow = ConfiguredKeycanWindow
keycan_app.KeycanWindow = ConfiguredKeycanWindow


if __name__ == "__main__":
    raise SystemExit(main())
