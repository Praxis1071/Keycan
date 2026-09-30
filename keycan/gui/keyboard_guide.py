"""Stage 9 keyboard guide for Keycan."""
from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk

from keycan.services.i18n import apply_to_widget_tree


class KeyboardGuidePanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_halign(Gtk.Align.FILL)
        self._build()

    def _build(self) -> None:
        title = Gtk.Label(label="Klavye Rehberi")
        title.set_xalign(0)
        title.add_css_class("title-1")
        self.append(title)

        intro = Gtk.Label(
            label="10 parmak yazmayı öğrenmek için doğru el pozisyonunu ve düzenli pratiği adım adım takip et."
        )
        intro.set_xalign(0)
        intro.set_wrap(True)
        intro.add_css_class("dim-label")
        self.append(intro)

        basics = Adw.PreferencesGroup()
        basics.set_title("Başlangıç")
        basics.set_description("Pratiğe başlamadan önce temel pozisyonu öğren.")
        self.append(basics)
        self._row(basics, "Ana sıra", "Sol el ASDF, sağ el JKLŞ tuşlarında; başparmaklar boşluk tuşuna yakın durur.")
        self._row(basics, "F ve J çıkıntıları", "İşaret parmaklarını F ve J üzerindeki fiziksel çıkıntılarla yönlendir.")
        self._row(basics, "Duruş", "Bileklerini rahat ve düz tut, omuzlarını gevşet ve ekrana doğal bir mesafeden bak.")

        fingers = Adw.PreferencesGroup()
        fingers.set_title("Parmak görevleri")
        fingers.set_description("Her parmağın kendi tuş alanına mümkün olduğunca sadık kal.")
        self.append(fingers)
        self._row(fingers, "Sol serçe", "Q · A · Z · 1 · Tab · Caps Lock · Shift")
        self._row(fingers, "Sol yüzük", "W · S · X · 2")
        self._row(fingers, "Sol orta", "E · D · C · 3")
        self._row(fingers, "Sol işaret", "R · F · V · T · G · B · 4 · 5")
        self._row(fingers, "Sağ işaret", "Y · H · N · U · J · M · 6 · 7")
        self._row(fingers, "Sağ orta", "I · K · , · 8")
        self._row(fingers, "Sağ yüzük", "O · L · . · 9")
        self._row(fingers, "Sağ serçe", "P · Ö · Ü · Ç · Ğ · , · 0 · Enter · Shift")

        practice = Adw.PreferencesGroup()
        practice.set_title("Çalışma yöntemi")
        practice.set_description("Hızdan önce doğruluğu ve rahatlığı koru.")
        self.append(practice)
        self._row(practice, "1. Adım", "Önce ana sırayı kullanarak parmaklarını doğru konuma yerleştir.")
        self._row(practice, "2. Adım", "Klavyeye bakmadan kısa kelimeler ve basit metinlerle başla.")
        self._row(practice, "3. Adım", "Yanlışları düzeltmeye ve aynı tuşa doğru parmakla basmaya odaklan.")
        self._row(practice, "4. Adım", "Doğruluğun istikrarlı hale geldiğinde hızını kademeli olarak artır.")
        self._row(practice, "5. Adım", "Keycan Çalışma Alanında düzenli ve kısa pratikler yap.")

        rows = Adw.PreferencesGroup()
        rows.set_title("Klavye sıraları")
        rows.set_description("Tuşları satır satır öğren ve parmak hareketlerini küçük tut.")
        self.append(rows)
        self._row(rows, "Üst sıra", "Q W E R T Y U I O P")
        self._row(rows, "Ana sıra", "A S D F G H J K L Ş İ")
        self._row(rows, "Alt sıra", "Z X C V B N M Ö Ç .")
        self._row(rows, "Boşluk", "Başparmaklardan biriyle rahatça ve gereksiz hareket etmeden kullan.")

    @staticmethod
    def _row(group, title: str, description: str) -> None:
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(description)
        group.add(row)

    def set_language(self, language: str) -> None:
        apply_to_widget_tree(self, language)
