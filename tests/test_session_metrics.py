from __future__ import annotations

from keycan.core.session_metrics import calculate_session_metrics
from keycan.core.typing_engine import TypingEngine
from keycan.services.session_recorder import SessionRecorder


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



class _FakeDatabase:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []
        self.failures_remaining = 0

    def save_result(self, **payload: object) -> None:
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise RuntimeError("temporary failure")
        self.saved.append(dict(payload))


def test_session_recorder_retries_failed_writes_without_changing_session_id() -> None:
    database = _FakeDatabase()
    database.failures_remaining = 1
    recorder = SessionRecorder(database)
    payload = {"lesson_id": 7, "session_uuid": "stable-session"}

    error = recorder.save(payload)

    assert isinstance(error, RuntimeError)
    assert recorder.pending_saves == [payload]
    assert database.saved == []

    failures = recorder.retry_pending()

    assert failures == []
    assert recorder.pending_saves == []
    assert database.saved == [payload]
    assert database.saved[0]["session_uuid"] == "stable-session"


def test_session_recorder_keeps_payloads_pending_when_retry_fails() -> None:
    database = _FakeDatabase()
    database.failures_remaining = 2
    recorder = SessionRecorder(database)
    payload = {"lesson_id": 8, "session_uuid": "retry-session"}

    assert isinstance(recorder.save(payload), RuntimeError)
    failures = recorder.retry_pending()

    assert len(failures) == 1
    assert failures[0][0] == payload
    assert isinstance(failures[0][1], RuntimeError)
    assert recorder.pending_saves == [payload]
    assert database.saved == []
