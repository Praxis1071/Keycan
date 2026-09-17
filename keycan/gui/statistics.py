"""Real SQLite-backed practice statistics for Keycan."""

from __future__ import annotations

import math
from datetime import datetime
from typing import TYPE_CHECKING

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, GLib, Gtk

if TYPE_CHECKING:
    from keycan.data.database import Database


MONTHS = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


class ProgressChart(Gtk.DrawingArea):
    """Lightweight line chart used for the real practice time series."""

    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(720)
        self.set_content_height(270)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.points: list[tuple[str, float]] = []
        self.value_suffix = ""

    def set_points(self, points: list[tuple[str, float]], value_suffix: str = "") -> None:
        self.points = [point for point in points if math.isfinite(point[1])]
        self.value_suffix = value_suffix
        self.queue_draw()

    def _draw(self, _area: Gtk.DrawingArea, cr, width: int, height: int, _data=None) -> None:
        left = 52.0
        right = max(left + 1.0, width - 20.0)
        top = 20.0
        bottom = max(top + 1.0, height - 44.0)
        chart_width = right - left
        chart_height = bottom - top

        cr.set_line_width(1.0)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.18)
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - chart_height * fraction
            cr.move_to(left, y)
            cr.line_to(right, y)
            cr.stroke()

        if not self.points:
            cr.set_source_rgba(0.45, 0.45, 0.45, 0.55)
            cr.move_to(left, bottom)
            cr.line_to(right, bottom)
            cr.stroke()
            return

        values = [value for _, value in self.points]
        minimum = min(values)
        maximum = max(values)
        if math.isclose(minimum, maximum):
            padding = max(1.0, abs(maximum) * 0.08)
            minimum -= padding
            maximum += padding

        cr.set_font_size(10)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.8)
        for fraction in (0.0, 0.5, 1.0):
            value = minimum + (maximum - minimum) * fraction
            y = bottom - chart_height * fraction
            cr.move_to(4, y + 4)
            cr.show_text(f"{value:.0f}{self.value_suffix}")

        cr.set_source_rgba(0.2, 0.55, 0.75, 0.95)
        cr.set_line_width(2.5)
        for index, (_label, value) in enumerate(self.points):
            x = left if len(self.points) == 1 else left + chart_width * index / (len(self.points) - 1)
            y = bottom - chart_height * ((value - minimum) / (maximum - minimum))
            if index == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()

        for index, (label, value) in enumerate(self.points):
            x = left if len(self.points) == 1 else left + chart_width * index / (len(self.points) - 1)
            y = bottom - chart_height * ((value - minimum) / (maximum - minimum))
            cr.arc(x, y, 3.5, 0, math.tau)
            cr.fill()
            if len(self.points) <= 10 or index in (0, len(self.points) - 1):
                cr.set_source_rgba(0.45, 0.45, 0.45, 0.8)
                cr.set_font_size(10)
                cr.move_to(max(left, x - 20), height - 12)
                cr.show_text(label)
                cr.set_source_rgba(0.2, 0.55, 0.75, 0.95)


class StatisticsPanel(Gtk.Box):
    """Adaptive statistics page backed by the application's SQLite database."""

    PERIODS = ("Günlük", "Haftalık", "Aylık", "Yıllık", "Tümü")

    def __init__(self, database: Database) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.db = database
        self.selected_period = "Haftalık"

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(980)
        clamp.set_tightening_threshold(700)
        scrolled.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(28)
        content.set_margin_bottom(36)
        content.set_margin_start(20)
        content.set_margin_end(20)
        clamp.set_child(content)

        self._append_revealed(content, self._make_header(), 40)
        self._append_revealed(content, self._make_overview(), 90)
        self._append_revealed(content, self._make_period_selector(), 140)
        self._append_revealed(content, self._make_speed_section(), 190)
        self._append_revealed(content, self._make_accuracy_section(), 240)
        self._append_revealed(content, self._make_history_section(), 290)
        self.refresh()

    @staticmethod
    def _append_revealed(parent: Gtk.Box, child: Gtk.Widget, delay_ms: int) -> None:
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        revealer.set_transition_duration(180)
        revealer.set_reveal_child(False)
        revealer.set_child(child)
        parent.append(revealer)

        def reveal() -> bool:
            revealer.set_reveal_child(True)
            return GLib.SOURCE_REMOVE

        GLib.timeout_add(delay_ms, reveal)

    @staticmethod
    def _heading(title: str, subtitle: str | None = None) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("title-2")
        box.append(label)
        if subtitle:
            detail = Gtk.Label(label=subtitle)
            detail.set_xalign(0)
            detail.set_wrap(True)
            detail.add_css_class("dim-label")
            box.append(detail)
        return box

    def _make_header(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        title = Gtk.Label(label="İstatistikler")
        title.set_xalign(0)
        title.add_css_class("title-1")
        box.append(title)
        description = Gtk.Label(label="Yazma hızını, doğruluğunu ve çalışma geçmişini takip et.")
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        box.append(description)
        return box

    def _make_overview(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Genel durum"))
        group = Adw.PreferencesGroup()
        rows = []
        for title, subtitle in (
            ("Çalışmalar", "Henüz veri yok"),
            ("Toplam süre", "Henüz veri yok"),
            ("Toplam kelime", "Henüz veri yok"),
            ("Ortalama doğruluk", "Henüz veri yok"),
        ):
            row = Adw.ActionRow()
            row.set_title(title)
            row.set_subtitle(subtitle)
            group.add(row)
            rows.append(row)
        section.append(group)
        self.overview_rows = tuple(rows)
        return section

    def _make_period_selector(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        section.append(self._heading("Dönem"))

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        controls.add_css_class("linked")
        controls.set_hexpand(True)
        self.period_buttons: list[Gtk.ToggleButton] = []
        previous: Gtk.ToggleButton | None = None
        for period in self.PERIODS:
            button = Gtk.ToggleButton(label=period)
            button.set_hexpand(True)
            button.set_active(period == self.selected_period)
            if previous is not None:
                button.set_group(previous)
            button.connect("toggled", self._on_period_toggled, period)
            self.period_buttons.append(button)
            controls.append(button)
            previous = button
        section.append(controls)
        return section

    def _make_speed_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Yazma hızı", "Zaman içindeki değişim"))

        frame = Gtk.Frame()
        frame.add_css_class("card")
        frame.set_hexpand(True)
        chart_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        chart_box.set_margin_top(14)
        chart_box.set_margin_bottom(14)
        chart_box.set_margin_start(14)
        chart_box.set_margin_end(14)
        self.chart = ProgressChart()
        chart_box.append(self.chart)

        self.chart_empty = Gtk.Label(label="Tamamlanmış çalışmalar burada grafik olarak görünecek.")
        self.chart_empty.set_wrap(True)
        self.chart_empty.set_justify(Gtk.Justification.CENTER)
        self.chart_empty.add_css_class("dim-label")
        self.chart_empty.set_margin_top(8)
        self.chart_empty.set_margin_bottom(8)
        chart_box.append(self.chart_empty)
        frame.set_child(chart_box)
        section.append(frame)
        return section

    def _make_accuracy_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Doğruluk", "Doğru ve yanlış kelimelerin dağılımı"))

        group = Adw.PreferencesGroup()
        correct = Adw.ActionRow()
        correct.set_title("Doğru kelimeler")
        correct.set_subtitle("Henüz veri yok")
        group.add(correct)

        wrong = Adw.ActionRow()
        wrong.set_title("Yanlış kelimeler")
        wrong.set_subtitle("Henüz veri yok")
        group.add(wrong)

        accuracy = Adw.ActionRow()
        accuracy.set_title("Doğruluk")
        accuracy.set_subtitle("Henüz veri yok")
        group.add(accuracy)
        section.append(group)
        self.accuracy_rows = (correct, wrong, accuracy)
        return section

    def _make_history_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Son çalışmalar", "Tamamlanan çalışmaların ayrıntıları"))

        frame = Gtk.Frame()
        frame.add_css_class("card")
        table = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        for title in ("Tarih", "Ders", "Süre", "Sonuç", "Doğruluk", "Hız"):
            label = Gtk.Label(label=title)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.add_css_class("dim-label")
            header.append(label)
        table.append(header)
        table.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.history_rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        table.append(self.history_rows)
        self.history_empty = Gtk.Label(label="Henüz tamamlanmış çalışma yok")
        self.history_empty.set_xalign(0)
        self.history_empty.set_margin_top(14)
        self.history_empty.set_margin_bottom(14)
        self.history_empty.set_margin_start(16)
        self.history_empty.set_margin_end(16)
        self.history_empty.add_css_class("dim-label")
        table.append(self.history_empty)
        frame.set_child(table)
        section.append(frame)
        return section

    def _on_period_toggled(self, button: Gtk.ToggleButton, period: str) -> None:
        if button.get_active():
            self.selected_period = period
            self.refresh()

    @staticmethod
    def _duration_text(seconds: float) -> str:
        total = max(0, int(round(seconds)))
        if total < 60:
            return f"{total} sn"
        minutes, remainder = divmod(total, 60)
        if minutes < 60:
            return f"{minutes} dk" if remainder == 0 else f"{minutes} dk {remainder} sn"
        hours, minutes = divmod(minutes, 60)
        return f"{hours} sa {minutes} dk" if minutes else f"{hours} sa"

    @staticmethod
    def _date_text(value: datetime) -> str:
        return f"{value.day} {MONTHS[value.month - 1]} {value.year}, {value:%H:%M}"

    @staticmethod
    def _clear_box(box: Gtk.Box) -> None:
        child = box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            child.unparent()
            child = next_child

    @staticmethod
    def _history_row(item: dict[str, object]) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.set_margin_start(16)
        row.set_margin_end(16)
        row.set_margin_top(9)
        row.set_margin_bottom(9)
        values = (
            StatisticsPanel._date_text(item["completed_at"]),
            str(item["lesson_title"] or "Ders"),
            StatisticsPanel._duration_text(float(item["duration_seconds"])),
            f"{int(item['typed_word_count'])} kelime",
            f"%{float(item['accuracy_percent']):.0f}",
            f"Dakikada {float(item['words_per_minute']):.0f} kelime",
        )
        for value in values:
            label = Gtk.Label(label=value)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.set_wrap(True)
            row.append(label)
        return row

    def set_overview(self, practices: int, duration_text: str, words: int, accuracy: float) -> None:
        self.overview_rows[0].set_subtitle(str(practices))
        self.overview_rows[1].set_subtitle(duration_text)
        self.overview_rows[2].set_subtitle(str(words))
        self.overview_rows[3].set_subtitle(f"%{accuracy:.0f}")

    def set_speed_points(self, points: list[tuple[str, float]]) -> None:
        self.chart.set_points(points, "")
        self.chart_empty.set_visible(not bool(points))

    def set_accuracy(self, correct: int, wrong: int, percent: float) -> None:
        self.accuracy_rows[0].set_subtitle(str(correct))
        self.accuracy_rows[1].set_subtitle(str(wrong))
        self.accuracy_rows[2].set_subtitle(f"%{percent:.0f}")

    def set_history(self, history: list[dict[str, object]]) -> None:
        self._clear_box(self.history_rows)
        for item in history:
            self.history_rows.append(self._history_row(item))
        self.history_empty.set_visible(not bool(history))

    def refresh(self) -> None:
        stats = self.db.practice_statistics(self.selected_period)
        self.set_overview(
            int(stats["practices"]),
            self._duration_text(float(stats["duration_seconds"])),
            int(stats["total_words"]),
            float(stats["accuracy_percent"]),
        )
        self.set_speed_points(list(stats["speed_points"]))
        self.set_accuracy(
            int(stats["correct_words"]),
            int(stats["wrong_words"]),
            float(stats["accuracy_percent"]),
        )
        self.set_history(list(stats["history"]))
