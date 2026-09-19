"""Persistent user preferences for Keycan.

Preferences live outside the SQLite practice database so UI settings never
become part of user content, lesson data, statistics, or backups.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

class Preferences:
    """Small, version-tolerant JSON preference store."""

    DEFAULTS = {"theme": "system", "language": "tr"}

    def __init__(self) -> None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = config_home / "keycan" / "preferences.json"
        self.values = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(data, dict):
            return
        for key, default in self.DEFAULTS.items():
            value = data.get(key, default)
            if key == "theme" and value not in {"system", "light", "dark"}:
                value = default
            if key == "language" and value not in {"tr", "en"}:
                value = default
            self.values[key] = value

    def get(self, key: str) -> str:
        return str(self.values.get(key, self.DEFAULTS.get(key, "")))

    def set(self, key: str, value: str) -> None:
        if key not in self.DEFAULTS:
            raise KeyError(key)
        if key == "theme" and value not in {"system", "light", "dark"}:
            raise ValueError("Geçersiz tema.")
        if key == "language" and value not in {"tr", "en"}:
            raise ValueError("Geçersiz dil.")
        self.values[key] = value
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.values, ensure_ascii=False, indent=2) + "\n"
        fd, temporary = NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=".preferences-",
            delete=False,
        )
        try:
            with fd:
                fd.write(payload)
                fd.flush()
                os.fsync(fd.fileno())
            os.replace(temporary.name, self.path)
        finally:
            if os.path.exists(temporary.name):
                os.unlink(temporary.name)
