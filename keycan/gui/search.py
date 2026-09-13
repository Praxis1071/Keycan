"""Keycan GUI search components.

This module will contain reusable search widgets separated from the
application bootstrap layer during the refactor process.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class SourceSearchDropdown(Gtk.Box):
    """Source chooser widget with substring filtering.

    The widget intentionally does not know anything about databases or
    windows. It only reports selection changes through the callback.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self._entries = []
        self.selected = Gtk.INVALID_LIST_POSITION
        self.on_selected_changed = None

        self.button = Gtk.Button(label="Ders grubu seçin")
        self.button.connect("clicked", self._toggle)
        self.append(self.button)

        self.popover = Gtk.Popover()
        self.popover.set_parent(self.button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Ders grubu ara…")
        self.search_entry.connect("search-changed", self._filter)
        box.append(self.search_entry)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        box.append(self.list_box)

        self.popover.set_child(box)

    @staticmethod
    def _normalize(text):
        return text.casefold().replace("ı", "i")

    def set_model(self, model):
        self._entries = [(i, model.get_string(i)) for i in range(model.get_n_items())]
        self._rebuild()

    def _rebuild(self):
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)

        for index, name in self._entries:
            button = Gtk.Button(label=name)
            button.set_has_frame(False)
            button.connect("clicked", self._select, index)
            self.list_box.append(button)

        self._filter()

    def _filter(self, *_args):
        query = self._normalize(self.search_entry.get_text())
        child = self.list_box.get_first_child()
        while child:
            visible = not query or query in self._normalize(child.get_label())
            child.set_visible(visible)
            child = child.get_next_sibling()

    def _select(self, _button, index):
        self.selected = index
        self.button.set_label(self._entries[index][1])
        if self.on_selected_changed:
            self.on_selected_changed(self, None)
        self.popover.popdown()

    def _toggle(self, *_args):
        if self.popover.get_visible():
            self.popover.popdown()
        else:
            self.popover.popup()
            self.search_entry.grab_focus()
