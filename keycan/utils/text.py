from __future__ import annotations

import re
import unicodedata

SOURCE_PREFIX = re.compile(r"^REVERSE ENGINEERING[/\\]+", re.IGNORECASE)
WORD_PATTERN = re.compile(r"\S+")


def clean_source_name(name: str) -> str:
    return SOURCE_PREFIX.sub("", name, count=1)


def natural_sort_key(value: str) -> list[object]:
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def format_remaining(seconds: float) -> str:
    remaining = max(0, int(seconds + 0.999))
    minutes, seconds = divmod(remaining, 60)
    return f"{minutes:02d}:{seconds:02d}"


def normalize_word(word: str) -> str:
    return "".join(
        char.casefold()
        for char in word
        if not unicodedata.category(char).startswith("P")
    )
