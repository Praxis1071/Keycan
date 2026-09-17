"""Progress-focused statistics surface for Keycan.

Stage 2 owns presentation and interaction. Stage 3 will provide real SQLite
records through the small data-facing methods exposed here; this module never
invents measurements when there is no data.
"""

from __future__ import annotations

import math

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Cairo, Gtk


class ProgressChart(Gtk.DrawingArea):
    """Lightweight line-chart surface ready for real practice data."""

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

    def _draw(self, _area: Gtk.DrawingArea, cr: Cairo.Context, width: int, height: int) -> None:
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
            cr.set_line_width(1.0)
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

        for index, (_label, value) in enumerate(self.points):
            x = left if len(self.points) == 1 else left + chart_width * index / (len(self.points) - 1)
            y = bottom - chart_height * ((value - minimum) / (maximum - minimum))
            cr.arc(x, y, 3.5, 0, math.tau)
            cr.fill()


class StatisticsPanel(Gtk.Box):
    """Simple, adaptive progress page independent of SQLite."""

    PERIODS = ("Günlük", "Haftalık", "Aylık", "Yıllık", "Tümü")

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
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

        content.append(self._make_header())
        content.append(self._make_period_selector())
        content.append(self._make_speed_section())
        content.append(self._make_accuracy_section())
        content.append(self._make_history_section())

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

    def _make_period_selector(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        section.append(self._heading("Dönem"))

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        controls.add_css_class("linked")
        controls.set_hexpand(True)
        self.period_buttons: list[Gtk.ToggleButton] = []
        previous: Gtk.ToggleButton | None = None
        for index, period in enumerate(self.PERIODS):
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
        chart_box.set_margin_bottom(10)
        chart_box.set_margin_start(14)
        chart_box.set_margin_end(14)
        self.chart = ProgressChart()
        chart_box.append(self.chart)

        empty = Gtk.Label(label="Tamamlanmış çalışmalar burada grafik olarak görünecek.")
        empty.set_wrap(True)
        empty.set_justify(Gtk.Justification.CENTER)
        empty.add_css_class("dim-label")
        empty.set_margin_top(8)
        empty.set_margin_bottom(8)
        chart_box.append(empty)
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

        group = Adw.PreferencesGroup()
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
        group.add(header)

        empty = Adw.ActionRow()
        empty.set_title("Henüz tamamlanmış çalışma yok")
        empty.set_subtitle("İlk çalışmanı tamamladığında geçmişin burada görünecek")
        group.add(empty)
        section.append(group)
        self.history_group = group
        return section

    def _on_period_toggled(self, button: Gtk.ToggleButton, period: str) -> None:
        if button.get_active():
            self.selected_period = period
            self._on_period_changed(period)

    def _on_period_changed(self, _period: str) -> None:
        # Stage 3 will supply the corresponding SQLite series here.
        self.chart.set_points([])

    def set_speed_points(self, points: list[tuple[str, float]]) -> None:
        """Stage 3 hook for a real time series; no synthetic data is created."""
        self.chart.set_points(points, "")

    def set_accuracy(self, correct: int, wrong: int, percent: float) -> None:
        """Stage 3 hook for real accuracy values."""
        self.accuracy_rows[0].set_subtitle(f"{correct}")
        self.accuracy_rows[1].set_subtitle(f"{wrong}")
        self.accuracy_rows[2].set_subtitle(f"%{percent:.0f}")
