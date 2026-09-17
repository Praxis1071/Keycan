"""Lesson group editor for all Keycan content."""

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk


class ContentManagerWindow(Adw.Window):
    def __init__(self, parent: Gtk.Widget, database, on_changed=None) -> None:
        super().__init__(transient_for=parent, modal=True, title="Ders Gruplarını Yönet")
        self.db=database; self.on_changed=on_changed; self.selected_group_id=None; self.selected_lesson_id=None
        self.set_default_size(900,620); self.set_size_request(640,460); self._build(); self._refresh_groups()

    @staticmethod
    def _rows(list_box):
        row=list_box.get_first_child()
        while row: yield row; row=row.get_next_sibling()

    @staticmethod
    def _clear(list_box):
        row=list_box.get_first_child()
        while row: nxt=row.get_next_sibling(); row.unparent(); row=nxt

    def _build(self):
        toolbar=Adw.ToolbarView(); toolbar.add_top_bar(Adw.HeaderBar())
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12); root.set_margin_top(18); root.set_margin_bottom(18); root.set_margin_start(18); root.set_margin_end(18); toolbar.set_content(root); self.set_content(toolbar)
        panes=Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL); panes.set_wide_handle(True); panes.set_position(300); panes.set_vexpand(True); root.append(panes)
        left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); left.set_margin_end(12); panes.set_start_child(left)
        label=Gtk.Label(label="Ders grupları"); label.set_xalign(0); label.add_css_class("title-3"); left.append(label)
        self.group_list=Gtk.ListBox(); self.group_list.set_selection_mode(Gtk.SelectionMode.SINGLE); self.group_list.set_show_separators(False); self.group_list.set_vexpand(True); self.group_list.connect("row-selected",self._group_selected)
        scroll=Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_child(self.group_list); left.append(scroll)
        create=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6); self.group_entry=Gtk.Entry(); self.group_entry.set_placeholder_text("Yeni ders grubu adı"); self.group_entry.set_hexpand(True); create.append(self.group_entry); b=Gtk.Button(label="Oluştur"); b.connect("clicked",self._create_group); create.append(b); left.append(create)
        actions=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6); self.rename_button=Gtk.Button(label="Yeniden adlandır"); self.rename_button.connect("clicked",self._rename_group); self.delete_button=Gtk.Button(label="Grubu sil"); self.delete_button.add_css_class("destructive-action"); self.delete_button.connect("clicked",self._delete_group); actions.append(self.rename_button); actions.append(self.delete_button); left.append(actions)
        right=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); right.set_margin_start(12); panes.set_end_child(right)
        self.group_header=Gtk.Label(label="Bir ders grubu seçin"); self.group_header.set_xalign(0); self.group_header.add_css_class("title-3"); right.append(self.group_header)
        self.lesson_list=Gtk.ListBox(); self.lesson_list.set_selection_mode(Gtk.SelectionMode.SINGLE); self.lesson_list.set_show_separators(True); self.lesson_list.set_vexpand(True); self.lesson_list.connect("row-selected",self._lesson_selected)
        lesson_scroll=Gtk.ScrolledWindow(); lesson_scroll.set_vexpand(True); lesson_scroll.set_child(self.lesson_list); right.append(lesson_scroll)
        order=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6); self.up_button=Gtk.Button(label="Yukarı taşı"); self.down_button=Gtk.Button(label="Aşağı taşı"); self.up_button.connect("clicked",lambda _b:self._move(-1)); self.down_button.connect("clicked",lambda _b:self._move(1)); order.append(self.up_button); order.append(self.down_button); right.append(order)
        editor=Adw.PreferencesGroup(); editor.set_title("Seçili metin"); editor.set_description("Metinlerin numarası sırasına göre otomatik belirlenir."); right.append(editor)
        self.text_view=Gtk.TextView(); self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); self.text_view.set_vexpand(True); es=Gtk.ScrolledWindow(); es.set_min_content_height(140); es.set_vexpand(True); es.set_child(self.text_view); editor.add(es)
        buttons=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6); self.add_button=Gtk.Button(label="Yeni metin ekle"); self.save_button=Gtk.Button(label="Metni kaydet"); self.save_button.add_css_class("suggested-action"); self.delete_text_button=Gtk.Button(label="Metni sil"); self.delete_text_button.add_css_class("destructive-action"); self.add_button.connect("clicked",self._add); self.save_button.connect("clicked",self._save); self.delete_text_button.connect("clicked",self._delete); buttons.append(self.add_button); buttons.append(self.save_button); buttons.append(self.delete_text_button); right.append(buttons)
        self.status=Gtk.Label(label=""); self.status.set_xalign(0); self.status.set_wrap(True); self.status.add_css_class("dim-label"); root.append(self.status); self._set_group_controls(False); self._set_lesson_controls(False)

    def _refresh_groups(self):
        selected=self.selected_group_id; self._clear(self.group_list)
        for number,(group_id,name,_key,_is_custom) in enumerate(self.db.managed_groups(),1):
            row=Gtk.ListBoxRow(); row.group_id=group_id; l=Gtk.Label(label=self.db._display_source_name(name,number)); l.set_xalign(0); l.set_margin_top(10); l.set_margin_bottom(10); l.set_margin_start(10); l.set_margin_end(10); row.set_child(l); self.group_list.append(row)
            if group_id==selected:self.group_list.select_row(row)
        if self.group_list.get_selected_row() is None:self._clear_lessons()

    def _group_selected(self,_list,row):
        self.selected_group_id=getattr(row,"group_id",None) if row else None; self.selected_lesson_id=None
        if self.selected_group_id is None:self._clear_lessons();return
        group=next((g for g in self.db.managed_groups() if g[0]==self.selected_group_id),None); self.group_header.set_text(self.db._display_source_name(group[1],1) if group else "Ders grubu"); self._refresh_lessons(); self._set_group_controls(True)

    def _refresh_lessons(self):
        self._clear(self.lesson_list); self.selected_lesson_id=None
        if self.selected_group_id is None:self._set_lesson_controls(False);return
        lessons=self.db.managed_lessons(self.selected_group_id)
        for number,(lesson_id,_text,_key,_order,_is_custom) in enumerate(lessons,1):
            row=Gtk.ListBoxRow(); row.lesson_id=lesson_id; l=Gtk.Label(label=str(number)); l.set_xalign(0); l.set_margin_top(9); l.set_margin_bottom(9); l.set_margin_start(12); l.set_margin_end(12); row.set_child(l); self.lesson_list.append(row)
        if lessons:self.lesson_list.select_row(self.lesson_list.get_row_at_index(0))
        self._set_lesson_controls(bool(lessons))

    def _clear_lessons(self):
        self._clear(self.lesson_list); self.group_header.set_text("Bir ders grubu seçin"); self.selected_lesson_id=None; self.text_view.get_buffer().set_text(""); self._set_group_controls(False); self._set_lesson_controls(False)

    def _lesson_selected(self,_list,row):
        self.selected_lesson_id=getattr(row,"lesson_id",None) if row else None
        if self.selected_lesson_id is None:self.text_view.get_buffer().set_text(""); self._set_lesson_controls(False); return
        _id,_title,text=self.db.lesson(self.selected_lesson_id); self.text_view.get_buffer().set_text(text); self._set_lesson_controls(True)

    def _set_group_controls(self,enabled): self.rename_button.set_sensitive(enabled); self.delete_button.set_sensitive(enabled)
    def _set_lesson_controls(self,enabled): self.save_button.set_sensitive(enabled); self.delete_text_button.set_sensitive(enabled); self.up_button.set_sensitive(enabled); self.down_button.set_sensitive(enabled); self.add_button.set_sensitive(self.selected_group_id is not None)
    def _message(self,msg): self.status.set_text(msg)

    def _create_group(self,_b):
        try:self.selected_group_id=self.db.create_custom_group(self.group_entry.get_text())
        except ValueError as exc:self._message(str(exc));return
        self.group_entry.set_text(""); self._refresh_groups(); self._changed("Ders grubu oluşturuldu.")

    def _rename_group(self,_b):
        if self.selected_group_id is None:return
        try:self.db.rename_group(self.selected_group_id,self.group_entry.get_text())
        except ValueError as exc:self._message(str(exc));return
        self.group_entry.set_text(""); self._refresh_groups(); self._changed("Ders grubu yeniden adlandırıldı.")

    def _delete_group(self,_b):
        if self.selected_group_id is None:return
        dialog=Gtk.AlertDialog(message="Ders grubunu silmek istiyor musun?",detail="Grup ve içindeki metinler çalışma alanından kaldırılır. Çalışma geçmişi korunur."); dialog.set_buttons(["İptal","Sil"]); dialog.set_default_button(0); dialog.set_cancel_button(0); dialog.choose(self,None,self._delete_group_finish,None)

    def _delete_group_finish(self,dialog,result,_data):
        try:response=dialog.choose_finish(result)
        except Exception:return
        if response!=1:return
        try:self.db.delete_group(self.selected_group_id)
        except ValueError as exc:self._message(str(exc));return
        self.selected_group_id=None; self._clear_lessons(); self._refresh_groups(); self._changed("Ders grubu silindi.")

    def _text(self):
        b=self.text_view.get_buffer();return b.get_text(b.get_start_iter(),b.get_end_iter(),False)
    def _add(self,_b):
        if self.selected_group_id is None:return
        try:lesson_id=self.db.create_lesson(self.selected_group_id,self._text())
        except ValueError as exc:self._message(str(exc));return
        self.selected_lesson_id=lesson_id; self._refresh_lessons(); self._changed("Metin eklendi.")
    def _save(self,_b):
        if self.selected_lesson_id is None:return
        try:self.db.update_lesson(self.selected_lesson_id,self._text())
        except ValueError as exc:self._message(str(exc));return
        self._changed("Metin kaydedildi.")
    def _delete(self,_b):
        if self.selected_lesson_id is None:return
        dialog=Gtk.AlertDialog(message="Seçili metni silmek istiyor musun?",detail="Metin bu ders grubundan kaldırılır. Çalışma geçmişi korunur."); dialog.set_buttons(["İptal","Sil"]); dialog.set_default_button(0); dialog.set_cancel_button(0); dialog.choose(self,None,self._delete_finish,None)
    def _delete_finish(self,dialog,result,_data):
        try:response=dialog.choose_finish(result)
        except Exception:return
        if response!=1:return
        try:self.db.delete_lesson(self.selected_lesson_id)
        except ValueError as exc:self._message(str(exc));return
        self.selected_lesson_id=None; self._refresh_lessons(); self._changed("Metin silindi.")
    def _move(self,direction):
        if self.selected_lesson_id is None:return
        try:self.db.move_lesson(self.selected_lesson_id,direction)
        except ValueError as exc:self._message(str(exc));return
        current=self.selected_lesson_id; self._refresh_lessons()
        for row in self._rows(self.lesson_list):
            if getattr(row,"lesson_id",None)==current:self.lesson_list.select_row(row);break
        self._changed("Metin sırası güncellendi.")
    def _changed(self,msg):
        self.status.set_text(msg)
        if self.on_changed:self.on_changed()
