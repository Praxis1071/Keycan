"""User-created lesson group management for Keycan."""

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk

from keycan.data.database import Database


class ContentManagerWindow(Adw.Window):
    """Manage optional user lesson groups and their ordered text content."""

    def __init__(self, parent: Gtk.Widget, database: Database, on_changed) -> None:
        super().__init__(transient_for=parent, modal=True, title="Ders Gruplarını Yönet")
        self.db = database
        self.on_changed = on_changed
        self.selected_group_id: int | None = None
        self.selected_lesson_id: int | None = None
        self._loading = False
        self.set_default_size(900, 620)
        self.set_size_request(640, 460)
        self._build()
        self._refresh_groups()

    def _build(self) -> None:
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(18)
        root.set_margin_bottom(18)
        root.set_margin_start(18)
        root.set_margin_end(18)
        toolbar.set_content(root)
        self.set_content(toolbar)

        columns = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        columns.set_wide_handle(True)
        columns.set_position(300)
        columns.set_vexpand(True)
        root.append(columns)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.set_margin_end(12)
        columns.set_start_child(left)

        group_title = Gtk.Label(label="Ders gruplarım")
        group_title.set_xalign(0)
        group_title.add_css_class("title-3")
        left.append(group_title)

        self.group_list = Gtk.ListBox()
        self.group_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.group_list.set_show_separators(False)
        self.group_list.set_vexpand(True)
        self.group_list.connect("row-selected", self._on_group_selected)
        group_scroll = Gtk.ScrolledWindow()
        group_scroll.set_vexpand(True)
        group_scroll.set_child(self.group_list)
        left.append(group_scroll)

        group_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.group_name = Gtk.Entry()
        self.group_name.set_placeholder_text("Yeni ders grubu adı")
        self.group_name.set_hexpand(True)
        group_buttons.append(self.group_name)
        add_group = Gtk.Button(label="Oluştur")
        add_group.connect("clicked", self._create_group)
        group_buttons.append(add_group)
        left.append(group_buttons)

        group_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.rename_group_button = Gtk.Button(label="Yeniden adlandır")
        self.rename_group_button.connect("clicked", self._rename_group)
        self.delete_group_button = Gtk.Button(label="Grubu sil")
        self.delete_group_button.add_css_class("destructive-action")
        self.delete_group_button.connect("clicked", self._delete_group)
        group_actions.append(self.rename_group_button)
        group_actions.append(self.delete_group_button)
        left.append(group_actions)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_start(12)
        columns.set_end_child(right)

        self.group_header = Gtk.Label(label="Bir ders grubu seçin")
        self.group_header.set_xalign(0)
        self.group_header.add_css_class("title-3")
        right.append(self.group_header)

        self.lesson_list = Gtk.ListBox()
        self.lesson_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.lesson_list.set_show_separators(True)
        self.lesson_list.set_vexpand(True)
        self.lesson_list.connect("row-selected", self._on_lesson_selected)
        lesson_scroll = Gtk.ScrolledWindow()
        lesson_scroll.set_vexpand(True)
        lesson_scroll.set_child(self.lesson_list)
        right.append(lesson_scroll)

        reorder = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.up_button = Gtk.Button(label="Yukarı taşı")
        self.down_button = Gtk.Button(label="Aşağı taşı")
        self.up_button.connect("clicked", lambda _b: self._move_lesson(-1))
        self.down_button.connect("clicked", lambda _b: self._move_lesson(1))
        reorder.append(self.up_button)
        reorder.append(self.down_button)
        right.append(reorder)

        editor_group = Adw.PreferencesGroup()
        editor_group.set_title("Seçili metin")
        editor_group.set_description("Metinlerin numarası sıralarına göre otomatik belirlenir.")
        right.append(editor_group)

        self.editor = Gtk.TextView()
        self.editor.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.editor.set_vexpand(True)
        editor_scroll = Gtk.ScrolledWindow()
        editor_scroll.set_min_content_height(120)
        editor_scroll.set_vexpand(True)
        editor_scroll.set_child(self.editor)
        editor_group.add(editor_scroll)

        self.save_text_button = Gtk.Button(label="Metni kaydet")
        self.save_text_button.add_css_class("suggested-action")
        self.save_text_button.connect("clicked", self._save_lesson)
        self.add_text_button = Gtk.Button(label="Yeni metin ekle")
        self.add_text_button.connect("clicked", self._add_lesson)
        self.delete_text_button = Gtk.Button(label="Metni sil")
        self.delete_text_button.add_css_class("destructive-action")
        self.delete_text_button.connect("clicked", self._delete_lesson)
        text_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        text_actions.append(self.add_text_button)
        text_actions.append(self.save_text_button)
        text_actions.append(self.delete_text_button)
        right.append(text_actions)

        self.status = Gtk.Label(label="")
        self.status.set_xalign(0)
        self.status.add_css_class("dim-label")
        self.status.set_wrap(True)
        root.append(self.status)

        self._set_group_controls(False)
        self._set_lesson_controls(False)

    def _clear(self, box: Gtk.ListBox) -> None:
        child = box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            child.unparent()
            child = next_child

    def _refresh_groups(self) -> None:
        groups = self.db.custom_groups()
        selected = self.selected_group_id
        self._clear(self.group_list)
        self.selected_group_id = None
        for group_id, name, _key in groups:
            row = Gtk.ListBoxRow()
            row.group_id = group_id
            label = Gtk.Label(label=name)
            label.set_xalign(0)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            label.set_margin_start(10)
            label.set_margin_end(10)
            row.set_child(label)
            self.group_list.append(row)
            if group_id == selected:
                self.group_list.select_row(row)
        if self.group_list.get_selected_row() is None:
            self._clear_lessons()
        self._set_group_controls(self.group_list.get_selected_row() is not None)

    def _on_group_selected(self, _list, row) -> None:
        self.selected_group_id = getattr(row, "group_id", None) if row else None
        self.selected_lesson_id = None
        if self.selected_group_id is None:
            self._clear_lessons()
            return
        group = next((g for g in self.db.custom_groups() if g[0] == self.selected_group_id), None)
        self.group_header.set_text(group[1] if group else "Ders grubu")
        self._refresh_lessons()
        self._set_group_controls(True)

    def _refresh_lessons(self) -> None:
        self._clear(self.lesson_list)
        self.selected_lesson_id = None
        if self.selected_group_id is None:
            self._set_lesson_controls(False)
            return
        lessons = self.db.custom_lessons(self.selected_group_id)
        for index, (lesson_id, _text, _key, _order) in enumerate(lessons, 1):
            row = Gtk.ListBoxRow()
            row.lesson_id = lesson_id
            label = Gtk.Label(label=str(index))
            label.set_xalign(0)
            label.set_margin_top(9)
            label.set_margin_bottom(9)
            label.set_margin_start(12)
            label.set_margin_end(12)
            row.set_child(label)
            self.lesson_list.append(row)
        if lessons:
            self.lesson_list.select_row(self.lesson_list.get_row_at_index(0))
        self._set_lesson_controls(bool(lessons))

    def _clear_lessons(self) -> None:
        self._clear(self.lesson_list)
        self.group_header.set_text("Bir ders grubu seçin")
        self.selected_lesson_id = None
        self.editor.get_buffer().set_text("")
        self._set_group_controls(False)
        self._set_lesson_controls(False)

    def _on_lesson_selected(self, _list, row) -> None:
        self.selected_lesson_id = getattr(row, "lesson_id", None) if row else None
        if self.selected_lesson_id is None:
            self.editor.get_buffer().set_text("")
            self._set_lesson_controls(False)
            return
        _id, _title, text = self.db.lesson(self.selected_lesson_id)
        self.editor.get_buffer().set_text(text)
        self._set_lesson_controls(True)

    def _set_group_controls(self, enabled: bool) -> None:
        self.rename_group_button.set_sensitive(enabled)
        self.delete_group_button.set_sensitive(enabled)

    def _set_lesson_controls(self, enabled: bool) -> None:
        self.save_text_button.set_sensitive(enabled)
        self.delete_text_button.set_sensitive(enabled)
        self.up_button.set_sensitive(enabled)
        self.down_button.set_sensitive(enabled)
        self.add_text_button.set_sensitive(self.selected_group_id is not None)

    def _error(self, message: str) -> None:
        self.status.set_text(message)

    def _create_group(self, _button) -> None:
        try:
            group_id = self.db.create_custom_group(self.group_name.get_text())
        except ValueError as exc:
            self._error(str(exc))
            return
        self.group_name.set_text("")
        self.selected_group_id = group_id
        self._refresh_groups()
        for i in range(self.group_list.get_first_child().get_parent().get_first_child().get_parent().get_first_child().get_parent().get_first_child() if False else 0):
            pass
        for row in self._rows(self.group_list):
            if getattr(row, "group_id", None) == group_id:
                self.group_list.select_row(row)
                break
        self._changed("Ders grubu oluşturuldu.")

    @staticmethod
    def _rows(list_box: Gtk.ListBox):
        row = list_box.get_first_child()
        while row:
            yield row
            row = row.get_next_sibling()

    def _rename_group(self, _button) -> None:
        if self.selected_group_id is None:
            return
        try:
            self.db.rename_custom_group(self.selected_group_id, self.group_name.get_text())
        except ValueError as exc:
            self._error(str(exc))
            return
        self.group_name.set_text("")
        self._refresh_groups()
        self._changed("Ders grubu yeniden adlandırıldı.")

    def _delete_group(self, _button) -> None:
        if self.selected_group_id is None:
            return
        dialog = Gtk.AlertDialog(
            message="Ders grubunu silmek istiyor musun?",
            detail="Grup gizlenir ve içindeki metinler artık çalışma alanında görünmez. Tamamlanan çalışma geçmişi korunur.",
        )
        dialog.set_buttons(["İptal", "Sil"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        dialog.choose(self, None, self._delete_group_finish, None)

    def _delete_group_finish(self, dialog, result, _user_data) -> None:
        try:
            response = dialog.choose_finish(result)
        except Exception:
            return
        if response != "Sil":
            return
        try:
            self.db.delete_custom_group(self.selected_group_id)
        except ValueError as exc:
            self._error(str(exc))
            return
        self.selected_group_id = None
        self._clear_lessons()
        self._refresh_groups()
        self._changed("Ders grubu silindi.")

    def _add_lesson(self, _button) -> None:
        if self.selected_group_id is None:
            return
        buffer = self.editor.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        try:
            lesson_id = self.db.create_custom_lesson(self.selected_group_id, text)
        except ValueError as exc:
            self._error(str(exc))
            return
        self.selected_lesson_id = lesson_id
        self._refresh_lessons()
        for row in self._rows(self.lesson_list):
            if getattr(row, "lesson_id", None) == lesson_id:
                self.lesson_list.select_row(row)
                break
        self._changed("Metin eklendi.")

    def _save_lesson(self, _button) -> None:
        if self.selected_lesson_id is None:
            return
        buffer = self.editor.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        try:
            self.db.update_custom_lesson(self.selected_lesson_id, text)
        except ValueError as exc:
            self._error(str(exc))
            return
        self._changed("Metin kaydedildi.")

    def _delete_lesson(self, _button) -> None:
        if self.selected_lesson_id is None:
            return
        dialog = Gtk.AlertDialog(
            message="Seçili metni silmek istiyor musun?",
            detail="Metin bu ders grubundan kaldırılır.",
        )
        dialog.set_buttons(["İptal", "Sil"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        dialog.choose(self, None, self._delete_lesson_finish, None)

    def _delete_lesson_finish(self, dialog, result, _user_data) -> None:
        try:
            response = dialog.choose_finish(result)
        except Exception:
            return
        if response != "Sil":
            return
        try:
            self.db.delete_custom_lesson(self.selected_lesson_id)
        except ValueError as exc:
            self._error(str(exc))
            return
        self.selected_lesson_id = None
        self._refresh_lessons()
        self._changed("Metin silindi.")

    def _move_lesson(self, direction: int) -> None:
        if self.selected_lesson_id is None:
            return
        try:
            self.db.move_custom_lesson(self.selected_lesson_id, direction)
        except ValueError as exc:
            self._error(str(exc))
            return
        self._refresh_lessons()
        for row in self._rows(self.lesson_list):
            if getattr(row, "lesson_id", None) == self.selected_lesson_id:
                self.lesson_list.select_row(row)
                break
        self._changed("Metin sırası güncellendi.")

    def _changed(self, message: str) -> None:
        self.status.set_text(message)
        if self.on_changed:
            self.on_changed()
