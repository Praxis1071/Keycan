"""Keycan settings with statistics and full lesson-content management."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from keycan.gui.content_manager2 import ContentManagerWindow


class SettingsPanel(Gtk.Box):
    def __init__(self, parent: Gtk.Widget, on_content_changed=None, on_statistics_changed=None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.parent_window=parent; self.on_content_changed=on_content_changed; self.on_statistics_changed=on_statistics_changed
        self.set_margin_top(20); self.set_margin_bottom(20); self.set_margin_start(20); self.set_margin_end(20)
        title=Gtk.Label(label="Ayarlar"); title.set_xalign(0); title.add_css_class("title-2"); self.append(title)
        data=Adw.PreferencesGroup(); data.set_title("Veri ve içerik"); data.set_description("Çalışma geçmişini ve tüm ders içeriklerini yönet."); self.append(data)
        self._action(data,"Ders gruplarını yönet","Keycan'ın hazır grupları dahil tüm grupları oluştur, düzenle, sırala ve çalış.","Yönet",self._content)
        self._action(data,"İstatistikleri dışa aktar","Çalışma geçmişini ve ders içeriklerini Keycan yedeği olarak kaydet.","Dışa aktar",self._export)
        self._action(data,"İstatistikleri içe aktar","Daha önce oluşturduğun Keycan yedeğini geri yükle.","İçe aktar",self._import)
        self._destructive(data,"İstatistikleri sıfırla","Tamamlanan tüm çalışma geçmişini kalıcı olarak sil.","Sıfırla",self._reset)
        self._destructive(data,"Tüm ders gruplarını ve metinleri sıfırla","Keycan'ın hazır içerikleri dahil tüm ders gruplarını ve metinlerini kaldır.","Tümünü sıfırla",self._reset_content)
        self._action(data,"Varsayılan ders gruplarını ve metinleri ekle","Keycan'ın ilk kurulumdaki hazır ders gruplarını ve metinlerini geri yükle.","Varsayılanları ekle",self._restore_defaults)
        self.status=Gtk.Label(label=""); self.status.set_xalign(0); self.status.set_wrap(True); self.status.add_css_class("dim-label"); self.append(self.status)
        about_title=Gtk.Label(label="Hakkında"); about_title.set_xalign(0); about_title.add_css_class("title-3"); self.append(about_title)
        about=Gtk.Label(label="Keycan, Linux üzerinde on parmak yazma pratiği yapmayı kolaylaştırmak için geliştirilmiş, sade ve açık kaynaklı bir projedir.\n\nGeliştirici: Praxis1071"); about.set_xalign(0); about.set_wrap(True); self.append(about)
        for uri,label in (("https://github.com/Praxis1071","GitHub profili: github.com/Praxis1071"),("https://www.youtube.com/@Praxis1071","YouTube kanalı: youtube.com/@Praxis1071")):
            link=Gtk.LinkButton(uri=uri,label=label); link.set_halign(Gtk.Align.START); self.append(link)

    @staticmethod
    def _action(group,title,subtitle,text,callback):
        row=Adw.ActionRow(); row.set_title(title); row.set_subtitle(subtitle); b=Gtk.Button(label=text); b.set_valign(Gtk.Align.CENTER); b.connect("clicked",callback); row.add_suffix(b); group.add(row)
    @staticmethod
    def _destructive(group,title,subtitle,text,callback):
        row=Adw.ActionRow(); row.set_title(title); row.set_subtitle(subtitle); b=Gtk.Button(label=text); b.add_css_class("destructive-action"); b.set_valign(Gtk.Align.CENTER); b.connect("clicked",callback); row.add_suffix(b); group.add(row)
    def _db(self): return getattr(self.parent_window,"db",None)
    def _content(self,_b):
        if self._db() is None:self.status.set_text("Veritabanına erişilemedi.");return
        ContentManagerWindow(self.parent_window,self._db(),self.on_content_changed).present()
    def _export(self,_b):
        if self._db() is None:self.status.set_text("Veritabanına erişilemedi.");return
        try:self._pending_export=self._db().export_data()
        except Exception as exc:self.status.set_text(f"Dışa aktarma hazırlanamadı: {exc}");return
        d=Gtk.FileDialog(); d.set_title("Keycan yedeğini kaydet"); d.set_initial_name("keycan-yedek.json"); d.save(self.parent_window,None,self._save_finish,None)
    def _save_finish(self,d,result,_data):
        try:file=d.save_finish(result)
        except Exception:return
        if file is None:return
        try:file.replace_contents(self._pending_export.encode("utf-8"),None,False,Gio.FileCreateFlags.REPLACE_DESTINATION,None);self.status.set_text(f"Yedek kaydedildi: {file.get_basename()}")
        except Exception as exc:self.status.set_text(f"Yedek kaydedilemedi: {exc}")
    def _import(self,_b):
        if self._db() is None:self.status.set_text("Veritabanına erişilemedi.");return
        d=Gtk.FileDialog();d.set_title("Keycan yedeğini seç");d.open(self.parent_window,None,self._open_finish,None)
    def _open_finish(self,d,result,_data):
        try:file=d.open_finish(result)
        except Exception:return
        if file is None:return
        try:
            raw,_=file.load_contents(None); imported,skipped=self._db().import_data(raw.decode("utf-8")); self.status.set_text(f"İçe aktarma tamamlandı: {imported} grup/metin kaydı işlendi"+(f", {skipped} kayıt atlandı." if skipped else "."));
            if self.on_content_changed:self.on_content_changed()
            if self.on_statistics_changed:self.on_statistics_changed()
        except Exception as exc:self.status.set_text(f"Yedek içe aktarılamadı: {exc}")
    def _reset(self,_b):
        d=Gtk.AlertDialog(message="İstatistikleri tamamen sıfırlamak istiyor musun?",detail="Tamamlanan tüm çalışma geçmişi kalıcı olarak silinir. Ders grupların ve metinlerin korunur.");d.set_buttons(["İptal","Sıfırla"]);d.set_default_button(0);d.set_cancel_button(0);d.choose(self.parent_window,None,self._reset_finish,None)
    def _reset_finish(self,d,result,_data):
        try:response=d.choose_finish(result)
        except Exception:return
        if response!=1:return
        try:count=self._db().reset_statistics();self.status.set_text(f"İstatistikler sıfırlandı. Silinen çalışma: {count}.")
        except Exception as exc:self.status.set_text(f"İstatistikler sıfırlanamadı: {exc}");return
        if self.on_statistics_changed:self.on_statistics_changed()
    def _reset_content(self,_b):
        d=Gtk.AlertDialog(message="Tüm ders gruplarını ve metinleri sıfırlamak istiyor musun?",detail="DİKKAT: Keycan'ın varsayılan hazır dersleri ve senin eklediğin tüm ders grupları ve metinler dahil bütün ders içeriği çalışma alanından kaldırılır. İstatistikler ve çalışma geçmişi silinmez. Varsayılan içerikleri daha sonra 'Varsayılan ders gruplarını ve metinleri ekle' ile geri getirebilirsin.");d.set_buttons(["İptal","Tümünü sıfırla"]);d.set_default_button(0);d.set_cancel_button(0);d.choose(self.parent_window,None,self._reset_content_finish,None)
    def _reset_content_finish(self,d,result,_data):
        try:response=d.choose_finish(result)
        except Exception:return
        if response!=1:return
        try:
            groups,lessons=self._db().reset_all_content(); self.status.set_text(f"Tüm ders içeriği sıfırlandı. Kaldırılan grup: {groups}, metin: {lessons}.")
        except Exception as exc:self.status.set_text(f"Ders içeriği sıfırlanamadı: {exc}");return
        if self.on_content_changed:self.on_content_changed()
    def _restore_defaults(self,_b):
        d=Gtk.AlertDialog(message="Varsayılan ders grupları ve metinleri geri yüklensin mi?",detail="Keycan'ın ilk kurulumdaki hazır ders grupları ve metinleri geri getirilir. Çalışma geçmişin ve istatistiklerin korunur. Varsayılan gruplarda yaptığın değişiklikler geri alınır.");d.set_buttons(["İptal","Varsayılanları ekle"]);d.set_default_button(0);d.set_cancel_button(0);d.choose(self.parent_window,None,self._restore_defaults_finish,None)
    def _restore_defaults_finish(self,d,result,_data):
        try:response=d.choose_finish(result)
        except Exception:return
        if response!=1:return
        try:
            groups,lessons=self._db().restore_defaults(); self.status.set_text(f"Varsayılan içerik geri yüklendi: {groups} grup, {lessons} metin.")
        except Exception as exc:self.status.set_text(f"Varsayılan içerik geri yüklenemedi: {exc}");return
        if self.on_content_changed:self.on_content_changed()


class SettingsWindow(Adw.Window):
    def __init__(self,parent:Gtk.Widget)->None:
        super().__init__(transient_for=parent,modal=True,title="Ayarlar");self.set_default_size(520,500)
        toolbar=Adw.ToolbarView();toolbar.add_top_bar(Adw.HeaderBar())
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);scroll.set_child(SettingsPanel(parent));toolbar.set_content(scroll);self.set_content(toolbar)
