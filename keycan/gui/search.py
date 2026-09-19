"""Reusable source/ders grubu search widget for Keycan."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Pango


class SourceSearchDropdown(Gtk.Button):
    """Source chooser with reliable substring search inside its popover.

    The widget owns only its presentation and selection state. The parent
    window supplies the model and receives selection changes through the
    ``on_selected_changed`` callback.
    """

    def __init__(self) -> None:
        super().__init__()
        self.set_hexpand(True)
        self._entries: list[tuple[int, str]] = []
        self._rows: list[tuple[Gtk.ListBoxRow, int, str]] = []
        self.selected = Gtk.INVALID_LIST_POSITION
        self.on_selected_changed = None

        self.connect("clicked", self._toggle_popover)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_hexpand(True)
        button_box.set_halign(Gtk.Align.FILL)
        self.button_label = Gtk.Label()
        self.button_label.set_xalign(0)
        self.button_label.set_halign(Gtk.Align.FILL)
        self.button_label.set_hexpand(True)
        self.button_label.set_single_line_mode(True)
        self.button_label.set_ellipsize(Pango.EllipsizeMode.END)
        button_box.append(self.button_label)
        arrow = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        arrow.set_halign(Gtk.Align.END)
        button_box.append(arrow)
        self.set_child(button_box)

        self.popover = Gtk.Popover()
        self.popover.set_has_arrow(False)
        self.popover.set_autohide(True)
        self.popover.set_position(Gtk.PositionType.BOTTOM)
        self.popover.set_parent(self)

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        panel.set_margin_top(8)
        panel.set_margin_bottom(8)
        panel.set_margin_start(8)
        panel.set_margin_end(8)
        panel.set_size_request(700, 420)
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
        self.list_box.remove_all()
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
