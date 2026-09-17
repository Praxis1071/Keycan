"""Extended Keycan settings: statistics data and custom lesson groups."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from keycan.gui.content_manager import ContentManagerWindow


class SettingsPanel(Gtk.Box):
    def __init__(self, parent: Gtk.Widget, on_content_changed=None, on_statistics_changed=None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.parent_window = parent
        self.on_content_changed = on_content_changed
        self.on_statistics_changed = on_statistics_changed
        self.set_margin_top(20); self.set_margin_bottom(20); self.set_margin_start(20); self.set_margin_end(20)
        title = Gtk.Label(label="Ayarlar"); title.set_xalign(0); title.add_css_class("title-2"); self.append(title)

        group = Adw.PreferencesGroup(); group.set_title("Veri ve içerik"); group.set_description("Çalışma geçmişini ve kendi ders gruplarını yönet."); self.append(group)
        self._add_action(group, "Ders grupları", "Kendi gruplarını oluştur, düzenle, sırala ve çalış.", "Yönet", self._open_content_manager)
        self._add_action(group, "İstatistikleri dışa aktar", "Çalışma geçmişini ve kendi ders içeriklerini Keycan yedeği olarak kaydet.", "Dışa aktar", self._export_data)
        self._add_action(group, "İstatistikleri içe aktar", "Daha önce oluşturduğun Keycan yedeğini geri yükle.", "İçe aktar", self._import_data)
        row = Adw.ActionRow(); row.set_title("İstatistikleri sıfırla"); row.set_subtitle("Tamamlanan tüm çalışma geçmişini kalıcı olarak sil."); button = Gtk.Button(label="Sıfırla"); button.add_css_class("destructive-action"); button.set_valign(Gtk.Align.CENTER); button.connect("clicked", self._reset_statistics); row.add_suffix(button); group.add(row)
        self.status = Gtk.Label(label=""); self.status.set_xalign(0); self.status.set_wrap(True); self.status.add_css_class("dim-label"); self.append(self.status)

        about_title = Gtk.Label(label="Hakkında"); about_title.set_xalign(0); about_title.add_css_class("title-3"); self.append(about_title)
        about = Gtk.Label(label="Keycan, Linux üzerinde on parmak yazma pratiği yapmayı kolaylaştırmak için geliştirilmiş, sade ve açık kaynaklı bir projedir.\n\nGeliştirici: Praxis1071"); about.set_xalign(0); about.set_wrap(True); self.append(about)
        github = Gtk.LinkButton(uri="https://github.com/Praxis1071", label="GitHub profili: github.com/Praxis1071"); github.set_halign(Gtk.Align.START); self.append(github)
        youtube = Gtk.LinkButton(uri="https://www.youtube.com/@Praxis1071", label="YouTube kanalı: youtube.com/@Praxis1071"); youtube.set_halign(Gtk.Align.START); self.append(youtube)

    @staticmethod
    def _add_action(group, title, subtitle, button_text, callback):
        row = Adw.ActionRow(); row.set_title(title); row.set_subtitle(subtitle); button = Gtk.Button(label=button_text); button.set_valign(Gtk.Align.CENTER); button.connect("clicked", callback); row.add_suffix(button); group.add(row)
    def _db(self): return getattr(self.parent_window, "db", None)
    def _open_content_manager(self, _button):
        if self._db() is None: self.status.set_text("Veritabanına erişilemedi."); return
        ContentManagerWindow(self.parent_window, self._db(), self.on_content_changed).present()
    def _export_data(self, _button):
        if self._db() is None: self.status.set_text("Veritabanına erişilemedi."); return
        try: self._pending_export = self._db().export_data()
        except Exception as exc: self.status.set_text(f"Dışa aktarma hazırlanamadı: {exc}"); return
        dialog = Gtk.FileDialog(); dialog.set_title("Keycan yedeğini kaydet"); dialog.set_initial_name("keycan-yedek.json"); dialog.save(self.parent_window, None, self._save_file, None)
    def _save_file(self, dialog, result, _data):
        try: file = dialog.save_finish(result)
        except Exception: return
        if file is None:return
        try:
            file.replace_contents(self._pending_export.encode("utf-8"), None, False, Gio.FileCreateFlags.REPLACE_DESTINATION, None); self.status.set_text(f"Yedek kaydedildi: {file.get_basename()}")
        except Exception as exc:self.status.set_text(f"Yedek kaydedilemedi: {exc}")
    def _import_data(self, _button):
        dialog=Gtk.FileDialog(); dialog.set_title("Keycan yedeğini seç"); dialog.open(self.parent_window,None,self._open_file,None)
    def _open_file(self, dialog, result, _data):
        try:file=dialog.open_finish(result)
        except Exception:return
        if file is None:return
        try:
            raw,_etag=file.load_contents(None); imported,skipped=self._db().import_data(raw.decode("utf-8")); self.status.set_text(f"İçe aktarma tamamlandı: {imported} çalışma geri yüklendi" + (f", {skipped} kayıt atlandı." if skipped else "."))
            if self.on_content_changed:self.on_content_changed()
            if self.on_statistics_changed:self.on_statistics_changed()
        except Exception as exc:self.status.set_text(f"Yedek içe aktarılamadı: {exc}")
    def _reset_statistics(self,_button):
        dialog=Gtk.AlertDialog(message="İstatistikleri tamamen sıfırlamak istiyor musun?",detail="Tamamlanan tüm çalışma geçmişi kalıcı olarak silinir. Ders grupların ve metinlerin korunur."); dialog.set_buttons(["İptal","Sıfırla"]); dialog.set_default_button(0); dialog.set_cancel_button(0); dialog.choose(self.parent_window,None,self._reset_finish,None)
    def _reset_finish(self,dialog,result,_data):
        try:response=dialog.choose_finish(result)
        except Exception:return
        if response != 1:return
        try:
            count=self._db().reset_statistics(); self.status.set_text(f"İstatistikler sıfırlandı. Silinen çalışma: {count}.");
            if self.on_statistics_changed:self.on_statistics_changed()
        except Exception as exc:self.status.set_text(f"İstatistikler sıfırlanamadı: {exc}")


class SettingsWindow(Adw.Window):
    def __init__(self,parent:Gtk.Widget)->None:
        super().__init__(transient_for=parent,modal=True,title="Ayarlar"); self.set_default_size(520,500); self.set_size_request(420,360); toolbar=Adw.ToolbarView(); toolbar.add_top_bar(Adw.HeaderBar()); toolbar.set_content(SettingsPanel(parent)); self.set_content(toolbar)
