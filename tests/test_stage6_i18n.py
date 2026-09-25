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


def test_stage6_static_ui_strings_are_translated() -> None:
    samples = (
        ("Hakkında", "About"),
        ("Çalışma takvimi", "Practice calendar"),
        ("Son çalışmalar", "Recent sessions"),
        ("Ders bazlı performans", "Performance by lesson"),
        ("Ders grubu ara…", "Search lesson groups…"),
        ("Eşleşen ders grubu bulunamadı.", "No matching lesson group found."),
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
