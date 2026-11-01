"""Pure typing-session metrics, independent from GTK widget lifecycle."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from keycan.core.typing_engine import TypingEngine, TypingResult
from keycan.utils.text import WORD_PATTERN


@dataclass(frozen=True, slots=True)
class SessionMetrics:
    result: TypingResult
    duration_seconds: float
    target_word_count: int
    typed_word_count: int
    total_characters: int
    correct_characters: int
    wrong_characters: int
    words_per_minute: float
    characters_per_minute: float
    accuracy_percent: float
    wrong_letter_counts: dict[str, int]

    def to_save_payload(
        self,
        *,
        lesson_id: int,
        session_uuid: str,
    ) -> dict[str, object]:
        """Build the database payload without adding UI-specific state."""
        return {
            "lesson_id": lesson_id,
            "duration": self.duration_seconds,
            "correct": self.result.correct,
            "wrong": self.result.wrong,
            "target_word_count": self.target_word_count,
            "typed_word_count": self.typed_word_count,
            "total_characters": self.total_characters,
            "correct_characters": self.correct_characters,
            "wrong_characters": self.wrong_characters,
            "words_per_minute": self.words_per_minute,
            "characters_per_minute": self.characters_per_minute,
            "accuracy_percent": self.accuracy_percent,
            "wrong_letter_counts": dict(self.wrong_letter_counts),
            "session_uuid": session_uuid,
        }


def calculate_session_metrics(
    engine: TypingEngine,
    target_text: str,
    typed_text: str,
    elapsed_seconds: float,
) -> SessionMetrics:
    """Calculate the same word/character metrics used by saved practice rows."""
    result = engine.match_words(target_text, typed_text)
    target_word_count = len(WORD_PATTERN.findall(target_text))
    typed_word_count = len(WORD_PATTERN.findall(typed_text))
    total_characters = len(typed_text)
    character_correctness = engine.character_correctness(target_text, typed_text)
    correct_characters = sum(character_correctness)
    wrong_characters = total_characters - correct_characters

    minutes = elapsed_seconds / 60.0 if elapsed_seconds > 0 else 0.0
    words_per_minute = typed_word_count / minutes if minutes else 0.0
    characters_per_minute = total_characters / minutes if minutes else 0.0
    accuracy_percent = (
        result.correct / typed_word_count * 100.0 if typed_word_count else 0.0
    )

    wrong_letters = Counter()
    for index, typed_char in enumerate(typed_text):
        if index < len(target_text) and not character_correctness[index]:
            expected = target_text[index]
            if expected.isalpha():
                wrong_letters[expected.lower()] += 1
            elif typed_char.isalpha():
                wrong_letters[typed_char.lower()] += 1
    if len(typed_text) > len(target_text):
        for typed_char in typed_text[len(target_text):]:
            if typed_char.isalpha():
                wrong_letters[typed_char.lower()] += 1

    return SessionMetrics(
        result=result,
        duration_seconds=elapsed_seconds,
        target_word_count=target_word_count,
        typed_word_count=typed_word_count,
        total_characters=total_characters,
        correct_characters=correct_characters,
        wrong_characters=wrong_characters,
        words_per_minute=words_per_minute,
        characters_per_minute=characters_per_minute,
        accuracy_percent=accuracy_percent,
        wrong_letter_counts=dict(wrong_letters),
    )


__all__ = ["SessionMetrics", "calculate_session_metrics"]
