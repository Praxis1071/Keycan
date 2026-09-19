from __future__ import annotations

import json
from pathlib import Path

from keycan.services.preferences import Preferences


def test_preferences_default_to_system_theme_and_turkish(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    preferences = Preferences()
    assert preferences.get("theme") == "system"
    assert preferences.get("language") == "tr"


def test_preferences_persist_valid_theme_and_language(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    preferences = Preferences()
    preferences.set("theme", "dark")
    preferences.set("language", "en")

    restored = Preferences()
    assert restored.get("theme") == "dark"
    assert restored.get("language") == "en"
    assert json.loads(Path(restored.path).read_text(encoding="utf-8")) == {
        "theme": "dark",
        "language": "en",
    }


def test_preferences_reject_unknown_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    preferences = Preferences()
    try:
        preferences.set("theme", "purple")
        assert False
    except ValueError:
        pass
    try:
        preferences.set("language", "de")
        assert False
    except ValueError:
        pass
