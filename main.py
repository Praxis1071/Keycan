#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

import keycan.app as keycan_app
import keycan.window as keycan_window
from keycan.app import main


class SourceSearchDropdown(Gtk.Box):
    """Source chooser with reliable substring search inside its popover."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self._entries: list[tuple[int, str]] = []
        self._rows: list[tuple[Gtk.ListBoxRow, int, str]] = []
        self.selected = Gtk.INVALID_LIST_POSITION
        self.on_selected_changed = None

        self.button = Gtk.Button()
        self.button.set_hexpand(True)
        self.button.set_halign(Gtk.Align.FILL)
        self.button.set_valign(Gtk.Align.CENTER)
        self.button.connect("clicked", self._toggle_popover)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_hexpand(True)
        button_box.set_halign(Gtk.Align.FILL)
        self.button_label = Gtk.Label()
        self.button_label.set_xalign(0)
        self.button_label.set_halign(Gtk.Align.FILL)
        self.button_label.set_hexpand(True)
        button_box.append(self.button_label)
        arrow = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        arrow.set_halign(Gtk.Align.END)
        button_box.append(arrow)
        self.button.set_child(button_box)
        self.append(self.button)

        self.popover = Gtk.Popover()
        self.popover.set_has_arrow(False)
        self.popover.set_autohide(True)
        self.popover.set_position(Gtk.PositionType.BOTTOM)
        self.popover.set_parent(self.button)

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        panel.set_margin_top(8)
        panel.set_margin_bottom(8)
        panel.set_margin_start(8)
        panel.set_margin_end(8)
        panel.set_size_request(560, 420)
        self.popover.set_child(panel)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Ders grubu ara…")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_search_delay(100)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        panel.append(self.search_entry)
        panel.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        panel.append(self.scrolled)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.scrolled.set_child(self.list_box)

        self.empty_label = Gtk.Label(label="Eşleşen ders grubu bulunamadı.")
        self.empty_label.set_margin_top(16)
        self.empty_label.set_margin_bottom(16)
        self.empty_label.set_margin_start(12)
        self.empty_label.set_margin_end(12)
        self.empty_label.add_css_class("dim-label")
        self.empty_label.set_visible(False)
        panel.append(self.empty_label)
        self._update_button_label()

    @staticmethod
    def _search_key(text: str) -> str:
        return text.casefold().replace("ı", "i").replace("\u0307", "")

    def set_model(self, model: Gtk.StringList) -> None:
        self._entries = [
            (index, model.get_string(index))
            for index in range(model.get_n_items())
        ]
        self._rebuild_rows()

    def get_selected(self) -> int:
        return int(self.selected)

    def set_selected(self, index: int) -> None:
        index = int(index)
        if index != Gtk.INVALID_LIST_POSITION and not (0 <= index < len(self._entries)):
            index = Gtk.INVALID_LIST_POSITION
        if index == self.selected:
            self._update_button_label()
            return
        self.selected = index
        self._update_button_label()
        callback = self.on_selected_changed
        if callback is not None:
            callback(self, None)

    def _update_button_label(self) -> None:
        index = self.get_selected()
        if 0 <= index < len(self._entries):
            self.button_label.set_text(self._entries[index][1])
        else:
            self.button_label.set_text("Ders grubu seçin")

    def _rebuild_rows(self) -> None:
        while (child := self.list_box.get_first_child()) is not None:
            self.list_box.remove(child)
        self._rows.clear()
        for index, name in self._entries:
            row = Gtk.ListBoxRow()
            row.set_activatable(False)
            button = Gtk.Button()
            button.set_has_frame(False)
            button.set_hexpand(True)
            button.set_halign(Gtk.Align.FILL)
            label = Gtk.Label(label=name)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.set_wrap(True)
            label.set_margin_top(7)
            label.set_margin_bottom(7)
            label.set_margin_start(8)
            label.set_margin_end(8)
            button.set_child(label)
            button.connect("clicked", self._on_row_clicked, index)
            row.set_child(button)
            self.list_box.append(row)
            self._rows.append((row, index, name))
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._search_key(self.search_entry.get_text().strip())
        visible_count = 0
        for row, _index, name in self._rows:
            visible = not query or query in self._search_key(name)
            row.set_visible(visible)
            if visible:
                visible_count += 1
        self.empty_label.set_visible(visible_count == 0)

    def _on_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        self._apply_filter()

    def _on_search_activate(self, _entry: Gtk.SearchEntry) -> None:
        # Enter only performs the search; it never selects a result.
        self._apply_filter()

    def _on_row_clicked(self, _button: Gtk.Button, index: int) -> None:
        self.set_selected(index)
        self.popover.popdown()

    def _toggle_popover(self, _button: Gtk.Button) -> None:
        if self.popover.get_visible():
            self.popover.popdown()
        else:
            self._apply_filter()
            self.popover.popup()
            self.search_entry.grab_focus()


class ConfiguredKeycanWindow(keycan_window.KeycanWindow):
    def __init__(self, app: Adw.Application, database_path):
        super().__init__(app, database_path)
        self.maximize()
        self.text_size = 22
        self.size_spin.set_value(22)
        self._apply_text_size()

    def _build_ui(self) -> None:
        super()._build_ui()

        old_dropdown = self.source_dropdown
        parent = old_dropdown.get_parent()
        previous = old_dropdown.get_prev_sibling() if parent is not None else None
        self.source_dropdown = SourceSearchDropdown()
        self.source_dropdown.on_selected_changed = self._on_source_changed
        self.source_dropdown.set_hexpand(False)
        self.source_dropdown.set_halign(Gtk.Align.FILL)
        self.source_dropdown.set_size_request(576, -1)

        if parent is not None:
            old_dropdown.unparent()
            if previous is not None:
                self.source_dropdown.insert_after(parent, previous)
            else:
                parent.append(self.source_dropdown)

    def _load_sources(self) -> None:
        sources = self.db.sources(); self.source_ids = [i for i, _ in sources]; self.source_dropdown.set_model(Gtk.StringList.new([n for _, n in sources]))
        if sources: self.source_dropdown.set_selected(0)

    def _on_source_changed(self, _dropdown: SourceSearchDropdown, _param) -> None:
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids): self._load_lessons(self.source_ids[index])


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
        description = Gtk.Label(label="Keycan, Linux üzerinde on parmak yazma pratiği yapmayı kolaylaştırmak için geliştirilmiş, sade ve açık kaynaklı bir projedir.")
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
        thanks = Gtk.Label(label="Keycan projesine verdiği destek ve katkıları için Malik Özcan Hocam'a teşekkür ederim.")
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
