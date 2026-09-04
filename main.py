#!/usr/bin/env python3
"""Keycan için Linux masaüstü on parmak uygulaması."""

from __future__ import annotations

import html
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QElapsedTimer, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB = APP_DIR / "typing_data.db"
SOURCE_PREFIX = re.compile(r"^REVERSE ENGINEERING[/\\]+", re.IGNORECASE)
WORD_PATTERN = re.compile(r"\S+")


def clean_source_name(name: str) -> str:
    """Kaynak adının başındaki gereksiz proje klasörü adını yalnızca görünümde kaldırır."""
    return SOURCE_PREFIX.sub("", name, count=1)


def natural_sort_key(value: str) -> list[object]:
    """Kaynak adlarını sayıları da dikkate alarak doğal sırada sıralar."""
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def format_remaining(seconds: float) -> str:
    """Geri sayımı MM:SS biçiminde gösterir."""
    remaining = max(0, int(seconds + 0.999))
    minutes, seconds = divmod(remaining, 60)
    return f"{minutes:02d}:{seconds:02d}"


@dataclass
class Lesson:
    id: int
    title: str
    text: str


class Database:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self._migrate_results_schema()

    def _migrate_results_schema(self) -> None:
        """Eski veritabanlarında sonuç alanlarını geriye dönük uyumlu biçimde ekler."""
        columns = {
            row[1] for row in self.conn.execute("PRAGMA table_info(practice_results)")
        }
        additions = {
            "correct_words": "INTEGER NOT NULL DEFAULT 0",
            "wrong_words": "INTEGER NOT NULL DEFAULT 0",
            "words_per_minute": "REAL NOT NULL DEFAULT 0",
            "characters_per_minute": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.conn.execute(
                    f"ALTER TABLE practice_results ADD COLUMN {name} {definition}"
                )
        self.conn.commit()

    def sources(self) -> list[tuple[int, str]]:
        rows = self.conn.execute("SELECT id, display_name FROM sources").fetchall()
        cleaned_rows = [(source_id, clean_source_name(name)) for source_id, name in rows]
        return sorted(cleaned_rows, key=lambda row: natural_sort_key(row[1]))

    def lessons(self, source_id: int) -> list[tuple[int, str]]:
        rows = self.conn.execute(
            "SELECT id, title FROM lessons WHERE source_id = ? ORDER BY legacy_metin_id, id",
            (source_id,),
        ).fetchall()
        return [
            (lesson_id, f"Ders {index}")
            for index, (lesson_id, _title) in enumerate(rows, start=1)
        ]

    def lesson(self, lesson_id: int) -> Lesson:
        row = self.conn.execute(
            "SELECT id, title, text FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if not row:
            raise ValueError("Metin bulunamadı")
        return Lesson(*row)

    def save_result(
        self,
        lesson_id: int,
        duration: float,
        correct_words: int,
        wrong_words: int,
    ) -> None:
        """Sadece süre ve kelime sonuçlarını kaydeder; hız değerleri sıfır bırakılır."""
        self.conn.execute(
            """INSERT INTO practice_results(
                    lesson_id, duration_seconds, correct_chars, wrong_chars, wpm,
                    correct_words, wrong_words, words_per_minute, characters_per_minute
                ) VALUES (?, ?, 0, 0, 0, ?, ?, 0, 0)""",
            (lesson_id, duration, correct_words, wrong_words),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class TypingInput(QPlainTextEdit):
    character_typed = pyqtSignal(str)
    backspaced = pyqtSignal()

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.key() == Qt.Key.Key_Backspace:
            self.backspaced.emit()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.character_typed.emit("\n")
            return
        text = event.text()
        if text and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.character_typed.emit(text)


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.db = Database(database_path)
        self.current_lesson: Lesson | None = None
        self.typed = ""
        self.finished = False
        self.timer = QElapsedTimer()
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(100)
        self.stats_timer.timeout.connect(self._check_time)
        self.setWindowTitle("Keycan — On Parmak")
        self.resize(1200, 760)
        self._build_ui()
        self._load_sources()
        self.stats_timer.start()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Ders grubu:"))
        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self._load_lessons)
        controls.addWidget(self.source_combo, 2)

        controls.addWidget(QLabel("Metin:"))
        self.lesson_combo = QComboBox()
        self.lesson_combo.currentIndexChanged.connect(self._choose_lesson)
        controls.addWidget(self.lesson_combo, 1)

        controls.addWidget(QLabel("Süre:"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)
        self.duration_spin.setValue(1)
        self.duration_spin.setSuffix(" dakika")
        self.duration_spin.setToolTip("Çalışma süresini dakika olarak belirleyin.")
        self.duration_spin.valueChanged.connect(self._duration_changed)
        controls.addWidget(self.duration_spin)

        self.countdown_label = QLabel("01:00")
        self.countdown_label.setToolTip("Çalışma için kalan süre")
        countdown_font = QFont("Noto Sans", 13)
        countdown_font.setBold(True)
        self.countdown_label.setFont(countdown_font)
        controls.addWidget(self.countdown_label)

        self.restart_button = QPushButton("Baştan Başla")
        self.restart_button.clicked.connect(self._restart)
        controls.addWidget(self.restart_button)
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.target = QTextEdit()
        self.target.setReadOnly(True)
        self.target.setStyleSheet("background: white; color: black;")
        self.target.setFont(QFont("Noto Sans", 16))
        self.target.setMinimumHeight(280)
        splitter.addWidget(self.target)

        self.input = TypingInput()
        self.input.setPlaceholderText("Buraya yazmaya başlayın…")
        self.input.setStyleSheet("background: white; color: black;")
        self.input.setFont(QFont("Noto Sans Mono", 16))
        self.input.character_typed.connect(self._type_character)
        self.input.backspaced.connect(self._backspace)
        splitter.addWidget(self.input)
        splitter.setSizes([430, 180])
        layout.addWidget(splitter, 1)

        self.status = QLabel("Bir ders ve metin seçin.")
        layout.addWidget(self.status)

    def _load_sources(self) -> None:
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        for source_id, name in self.db.sources():
            self.source_combo.addItem(name, source_id)
        self.source_combo.blockSignals(False)
        if self.source_combo.count():
            self._load_lessons()

    def _load_lessons(self) -> None:
        source_id = self.source_combo.currentData()
        self.lesson_combo.blockSignals(True)
        self.lesson_combo.clear()
        if source_id is not None:
            for lesson_id, title in self.db.lessons(int(source_id)):
                self.lesson_combo.addItem(title, lesson_id)
        self.lesson_combo.blockSignals(False)
        self._choose_lesson()

    def _choose_lesson(self) -> None:
        lesson_id = self.lesson_combo.currentData()
        if lesson_id is not None:
            self.current_lesson = self.db.lesson(int(lesson_id))
            self._restart()

    def _duration_changed(self) -> None:
        if not self.timer.isValid() or self.finished:
            self.countdown_label.setText(format_remaining(self._duration_seconds()))

    def _restart(self) -> None:
        if not self.current_lesson:
            return
        self.typed = ""
        self.finished = False
        self.timer.invalidate()
        self.duration_spin.setEnabled(True)
        self.countdown_label.setText(format_remaining(self._duration_seconds()))
        self.input.clear()
        self.input.setEnabled(True)
        self._render_target_plain()
        self.status.setText("Yazmaya başlayınca geri sayım çalışır.")
        self.input.setFocus()

    def _type_character(self, character: str) -> None:
        if not self.current_lesson or self.finished:
            return

        if not self.timer.isValid():
            self.timer.start()
            self.duration_spin.setEnabled(False)

        if self._elapsed_seconds() >= self._duration_seconds():
            self._finish()
            return

        self.typed += character
        self.input.setPlainText(self.typed)
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.input.setTextCursor(cursor)
        self._render_target_plain()

    def _backspace(self) -> None:
        if not self.typed or self.finished:
            return
        self.typed = self.typed[:-1]
        self.input.setPlainText(self.typed)
        self._render_target_plain()

    def _render_target_plain(self) -> None:
        if not self.current_lesson:
            return
        self.target.setPlainText(self.current_lesson.text)

    def _match_words_any_order(self) -> tuple[set[int], list[bool]]:
        """Yazılan her kelimeyi metindeki henüz eşleşmemiş herhangi bir kelimeyle eşleştirir."""
        assert self.current_lesson is not None
        target_matches = list(WORD_PATTERN.finditer(self.current_lesson.text))
        typed_matches = list(WORD_PATTERN.finditer(self.typed))
        unused_target_indices = set(range(len(target_matches)))
        matched_target_indices: set[int] = set()
        typed_correct: list[bool] = []

        for typed_match in typed_matches:
            typed_word = typed_match.group()
            target_index = next(
                (
                    index
                    for index in sorted(unused_target_indices)
                    if target_matches[index].group() == typed_word
                ),
                None,
            )
            if target_index is None:
                typed_correct.append(False)
            else:
                typed_correct.append(True)
                unused_target_indices.remove(target_index)
                matched_target_indices.add(target_index)

        return matched_target_indices, typed_correct

    def _render_results(self) -> tuple[int, int]:
        """Süre bitince doğru hedef kelimeleri yeşil, yanlış yazılan kelimeleri kırmızı gösterir."""
        assert self.current_lesson is not None
        target = self.current_lesson.text
        target_matches = list(WORD_PATTERN.finditer(target))
        matched_target_indices, typed_correct = self._match_words_any_order()

        html_parts: list[str] = []
        cursor = 0
        for index, target_match in enumerate(target_matches):
            html_parts.append(html.escape(target[cursor : target_match.start()]).replace("\n", "<br>"))
            word = html.escape(target_match.group())
            if index in matched_target_indices:
                html_parts.append(f'<span style="color:#16803c;">{word}</span>')
            else:
                html_parts.append(word)
            cursor = target_match.end()
        html_parts.append(html.escape(target[cursor:]).replace("\n", "<br>"))
        self.target.setHtml("".join(html_parts))

        self._render_input_results(typed_correct)
        correct = sum(typed_correct)
        wrong = len(typed_correct) - correct
        return correct, wrong

    def _render_input_results(self, typed_correct: list[bool]) -> None:
        """Süre sonunda giriş alanındaki doğru kelimeleri yeşil, yanlışları kırmızı yapar."""
        cursor = self.input.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)
        cursor.clearSelection()

        matches = list(WORD_PATTERN.finditer(self.typed))
        for match, is_correct in zip(matches, typed_correct):
            word_cursor = self.input.textCursor()
            word_cursor.setPosition(match.start())
            word_cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setForeground(Qt.GlobalColor.darkGreen if is_correct else Qt.GlobalColor.red)
            word_cursor.setCharFormat(fmt)

    def _elapsed_seconds(self) -> float:
        return self.timer.elapsed() / 1000 if self.timer.isValid() else 0.0

    def _duration_seconds(self) -> int:
        return self.duration_spin.value() * 60

    def _check_time(self) -> None:
        if not self.timer.isValid() or self.finished:
            return
        remaining = self._duration_seconds() - self._elapsed_seconds()
        if remaining <= 0:
            self.countdown_label.setText("00:00")
            self._finish()
        else:
            self.countdown_label.setText(format_remaining(remaining))

    def _finish(self) -> None:
        if self.finished or not self.current_lesson:
            return
        self.finished = True
        self.countdown_label.setText("00:00")
        self.input.setEnabled(False)
        self.duration_spin.setEnabled(True)

        elapsed = min(self._elapsed_seconds(), float(self._duration_seconds()))
        correct_words, wrong_words = self._render_results()
        self.db.save_result(
            self.current_lesson.id,
            elapsed,
            correct_words,
            wrong_words,
        )
        self.status.setText(
            f"Süre doldu. Doğru: {correct_words}  |  Yanlış: {wrong_words}"
        )

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self.db.close()
        event.accept()


def main() -> int:
    database_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    if not database_path.exists():
        print(f"Veritabanı bulunamadı: {database_path}", file=sys.stderr)
        print("Önce data_loader.py komutunu çalıştırın.", file=sys.stderr)
        return 1
    app = QApplication(sys.argv)
    window = MainWindow(database_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
