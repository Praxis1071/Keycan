"""Pure translation catalog for Keycan's application-owned UI strings."""

from __future__ import annotations

import re

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


def translate(text: str, language: str) -> str:
    """Translate static and runtime-generated application UI text."""
    if language == "en":
        translated = TRANSLATIONS.get(text, text)
        return _translate_runtime_patterns(translated, "en")
    reverse = {translated: source for source, translated in TRANSLATIONS.items()}
    translated = reverse.get(text, text)
    return _translate_runtime_patterns(translated, "tr")


_RUNTIME_PATTERNS = (
    (r"^Doğru: (.+)$", r"Correct: \\1", r"^Correct: (.+)$", r"Doğru: \\1"),
    (r"^Yanlış: (.+)$", r"Wrong: \\1", r"^Wrong: (.+)$", r"Yanlış: \\1"),
    (r"^Dakikada (.+) kelime$", r"\\1 words per minute", r"^(.+) words per minute$", r"Dakikada \\1 kelime"),
    (r"^(.+) kelime/dk$", r"\\1 words/min", r"^(.+) words/min$", r"\\1 kelime/dk"),
    (r"^Şimdi: (.+) · Önceki: (.+) · Değişim: (.+)$", r"Now: \\1 · Previous: \\2 · Change: \\3", r"^Now: (.+) · Previous: (.+) · Change: (.+)$", r"Şimdi: \\1 · Önceki: \\2 · Değişim: \\3"),
    (r"^İlk: (.+)  →  Son: (.+)  \\((.+)\\)$", r"First: \\1  →  Latest: \\2  (\\3)", r"^First: (.+)  →  Latest: (.+)  \\((.+)\\)$", r"İlk: \\1  →  Son: \\2  (\\3)"),
    (r"^(.+) puan$", r"\\1 points", r"^(.+) points$", r"\\1 puan"),
    (r"^(.+) çalışma$", r"\\1 practice sessions", r"^(.+) practice sessions$", r"\\1 çalışma"),
    (r"^(.+) aktif gün · (.+) çalışma · (.+) toplam süre$", r"\\1 active days · \\2 practice sessions · \\3 total time", r"^(.+) active days · (.+) practice sessions · (.+) total time$", r"\\1 aktif gün · \\2 çalışma · \\3 toplam süre"),
    (r"^Henüz çalışma yok$", r"No practice yet", r"^No practice yet$", r"Henüz çalışma yok"),
    (r"^Henüz tamamlanmış çalışma yok$", r"No completed practice yet", r"^No completed practice yet$", r"Henüz tamamlanmış çalışma yok"),
    (r"^Henüz yeterli veri yok\\.$", r"Not enough data yet.", r"^Not enough data yet\\.$", r"Henüz yeterli veri yok."),
    (r"^Yeterli veri olduğunda gösterilir$", r"Shown when enough data is available", r"^Shown when enough data is available$", r"Yeterli veri olduğunda gösterilir"),
    (r"^En az iki çalışma olduğunda karşılaştırma gösterilir$", r"Comparison is shown after at least two practice sessions", r"^Comparison is shown after at least two practice sessions$", r"En az iki çalışma olduğunda karşılaştırma gösterilir"),
)


def _translate_runtime_patterns(text: str, language: str) -> str:
    if language == "en":
        for tr_pattern, en_replacement, _en_pattern, _tr_replacement in _RUNTIME_PATTERNS:
            if re.match(tr_pattern, text):
                return re.sub(tr_pattern, en_replacement, text)
        return text
    for _tr_pattern, _en_replacement, en_pattern, tr_replacement in _RUNTIME_PATTERNS:
        if re.match(en_pattern, text):
            return re.sub(en_pattern, tr_replacement, text)
    return text
