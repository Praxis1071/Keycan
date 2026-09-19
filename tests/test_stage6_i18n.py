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
