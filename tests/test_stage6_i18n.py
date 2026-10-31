from keycan.services.translations import translate


def test_stage6_translation_round_trip() -> None:
    assert translate("Ayarlar", "en") == "Settings"
    assert translate("Settings", "tr") == "Ayarlar"
    assert translate("Ayarlar", "tr") == "Ayarlar"
    assert translate("Unknown UI string", "en") == "Unknown UI string"


def test_stage6_translation_is_reversible_for_theme_labels() -> None:
    for source, expected in (("Sistem", "System"), ("Açık", "Light"), ("Koyu", "Dark")):
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_keyboard_guide_and_statistics_labels_are_translated() -> None:
    samples = (
        ("Klavye Rehberi", "Keyboard Guide"),
        ("Temel teknik", "Basic technique"),
        ("Ergonomi ve mola", "Ergonomics and breaks"),
        ("Güvenilir ve okunabilir kaynaklar", "Reliable, readable resources"),
        ("Şubat", "February"),
        ("Pzt", "Mon"),
        ("Toplam süre", "Total time"),
        ("Gelişmiş analiz", "Advanced analysis"),
    )
    for source, expected in samples:
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_stage6_runtime_text_is_fully_translated() -> None:
    samples = {
        "Doğru: 42": "Correct: 42",
        "Yanlış: 3": "Wrong: 3",
        "Dakikada 75 kelime": "75 words per minute",
        "Şimdi: 80 · Önceki: 70 · Değişim: +10": "Now: 80 · Previous: 70 · Change: +10",
        "Yeterli veri olduğunda gösterilir": "Shown when enough data is available",
    }
    for source, expected in samples.items():
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_statistics_and_profile_runtime_values_translate_recursively() -> None:
    samples = {
        "45 sn": "45 sec",
        "2 dk 30 sn": "2 min 30 sec",
        "3 sa 15 dk": "3 hr 15 min",
        "2026: 5 aktif gün · 10 çalışma · 2 sa 30 dk toplam süre": (
            "2026: 5 active days · 10 practice sessions · 2 hr 30 min total time"
        ),
        "5 çalışma · Dakikada 50 kelime · %95 doğruluk": (
            "5 practice sessions · 50 words per minute · 95% accuracy"
        ),
        "yeni hız rekoru: Dakikada 75 kelime": "new speed record: 75 words per minute",
        "2 / 5 rozet açıldı.": "2 / 5 badges unlocked.",
        "Sonraki seviye için 120 XP": "120 XP to the next level",
    }
    for source, expected in samples.items():
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_stage6_static_ui_strings_are_translated() -> None:
    samples = (
        ("Hakkında", "About"),
        ("Çalışma takvimi", "Practice calendar"),
        ("Son çalışmalar", "Recent sessions"),
        ("Ders bazlı performans", "Performance by lesson"),
        ("Ders grubu ara…", "Search lesson groups…"),
        ("Eşleşen ders grubu bulunamadı.", "No matching lesson group found."),
        ("Ders grubu seçin", "Select a lesson group"),
    )
    for source, expected in samples:
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_stage7_runtime_profile_text_is_translated_both_ways() -> None:
    samples = {
        "Seviye 3": "Level 3",
        "10 çalışma · 250 XP · 4 gün mevcut seri": "10 practice sessions · 250 XP · 4-day current streak",
        "İlk: 40  →  Son: 60  (50%)": "First: 40  →  Latest: 60  (50%)",
        "Henüz yeterli veri yok.": "Not enough data yet.",
    }
    for source, expected in samples.items():
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source


def test_stage6_workspace_runtime_status_is_translated() -> None:
    samples = {
        "Yazmaya başlayınca geri sayım çalışır.": "The countdown starts when you begin typing.",
        "Ders başladı. Yazmaya devam et.": "Practice started. Keep typing.",
        "Süre doldu. Doğru: 10  |  Yanlış: 2  |  Toplam: 12": "Time is up. Correct: 10  |  Wrong: 2  |  Total: 12",
    }
    for source, expected in samples.items():
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source

def test_shared_translation_catalog_covers_profile_and_reset_actions() -> None:
    from keycan.services.translations import translate as shared_translate

    samples = {
        "İstatistikleri ve profili sıfırla": "Reset statistics and profile progress",
        "Profil fotoğrafını kaldır": "Remove profile photo",
        "Çalışma kaydedildi ancak sonuç görünümü güncellenemedi.": (
            "Practice was saved, but the results view could not be refreshed."
        ),
        "Çalışma kaydedildi ancak profil görünümü güncellenemedi.": (
            "Practice was saved, but the profile view could not be refreshed."
        ),
        "İstatistiklere kaydedilemedi:": "Could not save to statistics:",
        "Çalışma tamamlandı ancak istatistiklere kaydedilemedi.": (
            "Practice finished, but the result could not be saved to statistics."
        ),
        "Ders grubunu silmek istiyor musun?": "Delete this lesson group?",
        "Seçili metni silmek istiyor musun?": "Delete the selected text?",
        "Veritabanına erişilemedi.": "Database could not be accessed.",
        "Varsayılan ders grupları ve metinleri geri yüklensin mi?": "Restore the default lesson groups and texts?",
        "Ders grubu bulunamadı": "Lesson group not found.",
        "Ders grubu adı boş olamaz": "Lesson group name cannot be empty.",
        "Metin bulunamadı": "Text not found.",
    }
    for source, expected in samples.items():
        assert shared_translate(source, "en") == expected
        assert shared_translate(expected, "tr") == source

def test_stage6_ambiguous_catalog_entries_round_trip_without_losing_source_text() -> None:
    samples = (
        ("Sonraki seviye için bir sonraki kilometre taşı.", "Your next level milestone."),
        ("Çalışma Alanı", "Workspace"),
        ("Çalışma alanı", "Typing workspace"),
        ("Bir ders grubu seçin", "Choose a lesson group"),
        ("Ders grubu seçin", "Select a lesson group"),
        ("Çalışma sayısı", "Practice count"),
        ("Çalışmalar", "Practice sessions"),
        ("rozet açıldı.", "badge unlocked."),
        ("rozetler açıldı.", "badges unlocked."),
        ("Yedek dosyası açılamadı:", "Could not open backup file:"),
        ("Ders 3", "Lesson 3"),
    )
    for source, expected in samples:
        assert translate(source, "en") == expected
        assert translate(expected, "tr") == source

