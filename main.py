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
        self._all_source_entries = []
        self._filtered_source_entries = []
        self._current_source_id = None
        self._updating_source_model = False
        super().__init__(app, database_path)

        # Keycan starts maximized so the main workspace fills the screen.
        self.maximize()

        # 22 is the default text size; the existing size control remains unchanged.
        self.text_size = 22
        self.size_spin.set_value(22)
        self._apply_text_size()

    def _build_ui(self) -> None:
        super()._build_ui()

        # Use an application-controlled search field instead of GTK DropDown's
        # internal search. This keeps filtering deterministic on the GNOME 50
        # runtime used by the Flatpak.
        parent = self.source_dropdown.get_parent()
        self.source_search = Gtk.SearchEntry()
        self.source_search.set_placeholder_text("Ders grubu ara…")
        self.source_search.set_tooltip_text(
            "Ders gruplarının başında, ortasında veya sonunda arama yap"
        )
        self.source_search.set_width_chars(18)
        self.source_search.set_hexpand(False)
        self.source_search.set_search_delay(100)
        self.source_search.connect("search-changed", self._on_source_search_changed)
        self.source_search.connect("activate", self._on_source_search_activate)

        if parent is not None:
            self.source_search.insert_after(parent, self.source_dropdown)

    @staticmethod
    def _source_search_key(text: str) -> str:
        # Make Turkish I/İ/ı variants behave consistently while preserving
        # normal Unicode case-insensitive matching for the rest of the text.
        return text.casefold().replace("ı", "i").replace("\u0307", "")

    def _load_sources(self) -> None:
        self._all_source_entries = self.db.sources()
        self._apply_source_filter(select_current=False)

    def _apply_source_filter(self, select_current: bool = True) -> None:
        query = self._source_search_key(self.source_search.get_text().strip())
        if query:
            filtered = [
                (source_id, name)
                for source_id, name in self._all_source_entries
                if query in self._source_search_key(name)
            ]
        else:
            filtered = list(self._all_source_entries)

        self._filtered_source_entries = filtered
        self.source_ids = [source_id for source_id, _name in filtered]

        self._updating_source_model = True
        try:
            self.source_dropdown.set_model(
                Gtk.StringList.new([name for _source_id, name in filtered])
            )

            if not filtered:
                self.source_dropdown.set_selected(Gtk.INVALID_LIST_POSITION)
            else:
                selected_index = 0
                if select_current and self._current_source_id is not None:
                    for index, (source_id, _name) in enumerate(filtered):
                        if source_id == self._current_source_id:
                            selected_index = index
                            break
                self.source_dropdown.set_selected(selected_index)
        finally:
            self._updating_source_model = False

        if not filtered:
            self._current_source_id = None
            self.lesson_ids = []
            self.lesson_dropdown.set_model(Gtk.StringList.new([]))
            self.current_lesson_id = None
            self.current_text = ""
            self._restart()
            self.status.set_text("Eşleşen ders grubu bulunamadı.")
            return

        if not select_current or self._current_source_id is None:
            source_id = filtered[0][0]
        else:
            source_id = filtered[selected_index][0]

        if source_id != self._current_source_id:
            self._current_source_id = source_id
            self._load_lessons(source_id)

    def _on_source_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        self._apply_source_filter(select_current=True)

    def _on_source_search_activate(self, _entry: Gtk.SearchEntry) -> None:
        # Enter selects the first matching group, so keyboard-only searching
        # behaves exactly like clicking a result.
        if self._filtered_source_entries:
            self.source_dropdown.set_selected(0)
            source_id = self._filtered_source_entries[0][0]
            if source_id != self._current_source_id:
                self._current_source_id = source_id
                self._load_lessons(source_id)

    def _on_source_changed(self, _dropdown: Gtk.DropDown, _param) -> None:
        if self._updating_source_model:
            return

        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self._filtered_source_entries):
            source_id, _name = self._filtered_source_entries[index]
            if source_id != self._current_source_id:
                self._current_source_id = source_id
                self._load_lessons(source_id)


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
