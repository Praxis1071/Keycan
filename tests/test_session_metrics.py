from __future__ import annotations

from keycan.core.session_metrics import calculate_session_metrics
from keycan.core.typing_engine import TypingEngine


def test_session_metrics_preserve_word_and_character_analysis() -> None:
    metrics = calculate_session_metrics(
        TypingEngine(),
        target_text="bir iki",
        typed_text="bir ucu",
        elapsed_seconds=60,
    )

    assert metrics.result.correct == 1
    assert metrics.result.wrong == 1
    assert metrics.target_word_count == 2
    assert metrics.typed_word_count == 2
    assert metrics.total_characters == 7
    assert metrics.correct_characters == 4
    assert metrics.wrong_characters == 3
    assert metrics.words_per_minute == 2
    assert metrics.characters_per_minute == 7
    assert metrics.accuracy_percent == 50
    assert metrics.wrong_letter_counts == {"i": 2, "k": 1}


def test_session_metrics_count_extra_letters_without_elapsed_time() -> None:
    metrics = calculate_session_metrics(
        TypingEngine(),
        target_text="abc",
        typed_text="abcd",
        elapsed_seconds=0,
    )

    assert metrics.total_characters == 4
    assert metrics.correct_characters == 3
    assert metrics.wrong_characters == 1
    assert metrics.words_per_minute == 0
    assert metrics.characters_per_minute == 0
    assert metrics.wrong_letter_counts == {"d": 1}


def test_session_metrics_builds_database_payload() -> None:
    metrics = calculate_session_metrics(
        TypingEngine(),
        target_text="bir iki",
        typed_text="bir iki",
        elapsed_seconds=30,
    )

    payload = metrics.to_save_payload(lesson_id=42, session_uuid="stable-session")

    assert payload == {
        "lesson_id": 42,
        "duration": 30,
        "correct": 2,
        "wrong": 0,
        "target_word_count": 2,
        "typed_word_count": 2,
        "total_characters": 7,
        "correct_characters": 7,
        "wrong_characters": 0,
        "words_per_minute": 4,
        "characters_per_minute": 14,
        "accuracy_percent": 100,
        "wrong_letter_counts": {},
        "session_uuid": "stable-session",
    }
