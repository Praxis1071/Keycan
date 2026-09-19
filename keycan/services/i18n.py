"""Centralized UI language support for Keycan.

The practice database and lesson content are deliberately excluded from this
layer. Only application-owned UI strings are translated.
"""

from __future__ import annotations

from gi.repository import Adw, Gtk


TRANSLATIONS = {
    "Ayarlar": "Settings",
    "Veri ve içerik": "Data and content",
    "Çalışma geçmişini ve tüm ders içeriklerini yönet.": "Manage practice history and all lesson content.",
    "Ders gruplarını yönet": "Manage lesson groups",
    "Keycan'ın hazır grupları dahil tüm grupları oluştur, düzenle, sırala ve çalış.": "Create, edit, reorder, and use all lesson groups, including Keycan's built-in groups.",
    "Yönet": "Manage",
    "İstatistikleri dışa aktar": "Export statistics",
    "Çalışma geçmişini ve ders içeriklerini Keycan yedeği olarak kaydet.": "Save practice history and lesson content as a Keycan backup.",
    "Dışa aktar": "Export",
    "İstatistikleri içe aktar": "Import statistics",
    "Daha önce oluşturduğun Keycan yedeğini geri yükle.": "Restore a previously created Keycan backup.",
    "İçe aktar": "Import",
    "İstatistikleri sıfırla": "Reset statistics",
    "Tamamlanan tüm çalışma geçmişini kalıcı olarak sil.": "Permanently delete all completed practice history.",
    "Sıfırla": "Reset",
    "Tüm ders gruplarını ve metinleri sıfırla": "Reset all lesson groups and texts",
    "Keycan'ın hazır içerikleri dahil tüm ders gruplarını ve metinlerini kaldır.": "Remove all lesson groups and texts, including Keycan's built-in content.",
    "Tümünü sıfırla": "Reset all",
    "Varsayılan ders gruplarını ve metinleri ekle": "Restore default lesson groups and texts",
    "Keycan'ın ilk kurulumdaki hazır ders gruplarını ve metinlerini geri yükle.": "Restore Keycan's default lesson groups and texts.",
    "Varsayılanları ekle": "Restore defaults",
    "Hakkında": "About",
    "Görünüm ve dil": "Appearance and language",
    "Keycan arayüzünün görünümünü ve dilini belirle.": "Choose Keycan's appearance and language.",
    "İptal": "Cancel",
    "Sil": "Delete",
    "Keycan yedeğini kaydet": "Save Keycan backup",
    "Keycan yedeğini seç": "Choose Keycan backup",

    "Ayarlar ve uygulama tercihleri": "Settings and application preferences",
    "Tema": "Theme",
    "Sistem": "System",
    "Açık": "Light",
    "Koyu": "Dark",
    "Dil": "Language",
    "Türkçe": "Turkish",
    "English": "English",
    "Değişiklik": "Change",
    "Dil değişikliği uygulamayı yeniden başlattığında uygulanır.": "The language change will take effect after restarting Keycan.",
    "Dil değişikliği hemen uygulandı.": "Language change applied immediately.",
    "Tema değişikliği hemen uygulanır.": "The theme change is applied immediately.",
    "Çalışma Alanı": "Workspace",
    "İstatistikler": "Statistics",
    "Yan paneli aç/kapat": "Toggle sidebar",
    "Ders grubu:": "Lesson group:",
    "Metin:": "Text:",
    "Süre:": "Duration:",
    "dakika": "minutes",
    "Baştan Başla": "Restart",
    "Tercihler": "Preferences",
    "Çalışma tercihleri": "Practice preferences",
    "Metin boyutu:": "Text size:",
    "Ders ve yazım metni boyutu": "Lesson and typing text size",
    "Bir ders ve metin seçin.": "Select a lesson and text.",
    "Yazmaya başlayınca geri sayım çalışır.": "The countdown starts when you begin typing.",
    "Ders başladı. Yazmaya devam et.": "Practice started. Keep typing.",
    "Süre doldu.": "Time is up.",
    "Doğru": "Correct",
    "Yanlış": "Wrong",
    "Toplam": "Total",
    "Yazım metnini karart": "Hide typed text",
    "Yazarken girdiğin metni gizler": "Hide the text you type while practicing",
    "Geri tuşunu devre dışı bırak": "Disable backspace",
    "Yazarken önceki karakteri silmeyi engeller": "Prevent deleting the previous character while typing",
    "Ders Gruplarını Yönet": "Manage Lesson Groups",
    "Ders grupları": "Lesson groups",
    "Yeni ders grubu adı": "New lesson group name",
    "Oluştur": "Create",
    "Yeniden adlandır": "Rename",
    "Grubu sil": "Delete group",
    "Bir ders grubu seçin": "Select a lesson group",
    "Yukarı taşı": "Move up",
    "Aşağı taşı": "Move down",
    "Seçili metin": "Selected text",
    "Metinlerin numarası sırasına göre otomatik belirlenir.": "Text numbers are assigned automatically by order.",
    "Yeni metin ekle": "Add text",
    "Metni kaydet": "Save text",
    "Metni sil": "Delete text",
    "Dönem": "Period",
    "Günlük": "Daily",
    "Haftalık": "Weekly",
    "Aylık": "Monthly",
    "Yıllık": "Yearly",
    "Tümü": "All time",
    "Genel": "Overview",
    "Gelişim": "Progress",
    "Dersler": "Lessons",
    "Hatalar": "Errors",
    "Rekorlar": "Records",
    "Yazma hızı": "Typing speed",
    "Doğruluk": "Accuracy",
    "Çalışma süresi": "Practice time",
    "Çalışma sayısı": "Practice sessions",
    "Toplam kelime": "Total words",
    "Toplam karakter": "Total characters",
    "Çalışma takvimi": "Practice calendar",
    "Kişisel rekorlar": "Personal records",
    "En yüksek hız": "Highest speed",
    "En yüksek doğruluk": "Highest accuracy",
    "En uzun çalışma": "Longest practice",
    "En yoğun gün": "Busiest day",
    "Tarih": "Date",
    "Ders": "Lesson",
    "Süre": "Duration",
    "Sonuç": "Result",
    "Hız": "Speed",
    "Daha az": "Less",
    "Daha fazla": "More",
    "Çalışma yok": "No practice",
    "Yıl": "Year",
    "Henüz çalışma yok": "No practice yet",
    "Ortalama hız": "Average speed",
}


def translate(text: str, language: str) -> str:
    """Translate application-owned UI text in either direction."""
    if language == "en":
        return TRANSLATIONS.get(text, text)
    reverse = {translated: source for source, translated in TRANSLATIONS.items()}
    return reverse.get(text, text)


def apply_to_widget_tree(root: Gtk.Widget, language: str) -> None:
    """Translate application-owned widget labels without touching lesson data."""
    stack = [root]
    while stack:
        widget = stack.pop()
        for child in _children(widget):
            stack.append(child)

        if isinstance(widget, Gtk.Label):
            _set_text(widget, language)
        elif isinstance(widget, Gtk.Button):
            _set_text(widget, language)
            _set_tooltip(widget, language)
        elif isinstance(widget, Gtk.ToggleButton):
            _set_text(widget, language)
        elif isinstance(widget, Gtk.Entry):
            placeholder = widget.get_placeholder_text()
            if placeholder:
                widget.set_placeholder_text(translate(placeholder, language))
        elif isinstance(widget, Gtk.SpinButton):
            _set_tooltip(widget, language)
        elif isinstance(widget, Adw.ComboRow):
            _translate_string_list(widget.get_model(), language)
        elif isinstance(widget, Adw.ActionRow):
            _set_title_subtitle(widget, language)
        elif isinstance(widget, Adw.PreferencesGroup):
            _set_title_description(widget, language)


def _children(widget: Gtk.Widget) -> list[Gtk.Widget]:
    result = []
    child = widget.get_first_child()
    while child is not None:
        result.append(child)
        child = child.get_next_sibling()
    return result


def _set_text(widget: Gtk.Widget, language: str) -> None:
    if not hasattr(widget, "get_label") or not hasattr(widget, "set_label"):
        return
    current = widget.get_label()
    if current:
        widget.set_label(translate(current, language))


def _set_tooltip(widget: Gtk.Widget, language: str) -> None:
    tooltip = widget.get_tooltip_text()
    if tooltip:
        widget.set_tooltip_text(translate(tooltip, language))


def _translate_string_list(model, language: str) -> None:
    if not isinstance(model, Gtk.StringList):
        return
    for index in range(model.get_n_items()):
        item = model.get_string(index)
        translated = translate(item, language)
        if translated != item:
            model.splice(index, 1, [translated])


def _set_title_subtitle(row: Adw.ActionRow, language: str) -> None:
    title, subtitle = row.get_title(), row.get_subtitle()
    if title:
        row.set_title(translate(title, language))
    if subtitle:
        row.set_subtitle(translate(subtitle, language))


def _set_title_description(group: Adw.PreferencesGroup, language: str) -> None:
    title, description = group.get_title(), group.get_description()
    if title:
        group.set_title(translate(title, language))
    if description:
        group.set_description(translate(description, language))
