"""Persistence queue for completed typing sessions."""

from __future__ import annotations

from typing import Any


class SessionRecorder:
    """Save completed sessions and retain failed writes for safe retry.

    The recorder keeps the same session UUID in each queued payload, allowing
    the database's uniqueness guard to make retries idempotent after an
    ambiguous commit outcome.
    """

    def __init__(self, database: Any) -> None:
        self._database = database
        self.pending_saves: list[dict[str, object]] = []

    def save(self, payload: dict[str, object]) -> Exception | None:
        try:
            self._database.save_result(**payload)
        except Exception as exc:
            self.pending_saves.append(dict(payload))
            return exc
        return None

    def retry_pending(self) -> list[tuple[dict[str, object], Exception]]:
        remaining: list[dict[str, object]] = []
        failures: list[tuple[dict[str, object], Exception]] = []
        for payload in self.pending_saves:
            try:
                self._database.save_result(**payload)
            except Exception as exc:
                remaining.append(payload)
                failures.append((payload, exc))
        self.pending_saves = remaining
        return failures


__all__ = ["SessionRecorder"]
