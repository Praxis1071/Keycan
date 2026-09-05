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
        unused = set(range(len(target_matches)))
        matched: set[int] = set()
        correctness: list[bool] = []

        for typed_match in typed_matches:
            typed_word = normalize_word(typed_match.group())
            target_index = next(
                (
                    index
                    for index in sorted(unused)
                    if typed_word
                    and normalize_word(target_matches[index].group()) == typed_word
                ),
                None,
            )
            if target_index is None:
                correctness.append(False)
            else:
                correctness.append(True)
                unused.remove(target_index)
                matched.add(target_index)

        return TypingResult(matched, correctness)
