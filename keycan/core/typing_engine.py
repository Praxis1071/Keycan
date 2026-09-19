from __future__ import annotations

from dataclasses import dataclass

from keycan.utils.text import WORD_PATTERN, normalize_word


@dataclass(frozen=True)
class TypingResult:
    matched_target_indices: set[int]
    correctness: list[bool]

    @property
    def correct(self) -> int:
        return sum(self.correctness)

    @property
    def wrong(self) -> int:
        return len(self.correctness) - self.correct


class TypingEngine:
    """GTK bağımsız yazım eşleştirme motoru."""

    def match_words(self, target_text: str, typed_text: str) -> TypingResult:
        target_matches = list(WORD_PATTERN.finditer(target_text))
        typed_matches = list(WORD_PATTERN.finditer(typed_text))
        matched: set[int] = set()
        correctness: list[bool] = []

        for index, typed_match in enumerate(typed_matches):
            typed_word = normalize_word(typed_match.group())
            if index >= len(target_matches):
                correctness.append(False)
                continue
            target_word = normalize_word(target_matches[index].group())
            is_correct = bool(typed_word) and typed_word == target_word
            correctness.append(is_correct)
            if is_correct:
                matched.add(index)

        return TypingResult(matched, correctness)

    def character_correctness(self, target_text: str, typed_text: str) -> list[bool]:
        """Return case-insensitive correctness for each typed character."""
        return [
            index < len(target_text) and character.casefold() == target_text[index].casefold()
            for index, character in enumerate(typed_text)
        ]
