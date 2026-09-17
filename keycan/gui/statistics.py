"""Polished, SQLite-backed practice statistics for Keycan."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
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
WEEKDAYS = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")


class ProgressChart(Gtk.DrawingArea):
    """A calm line chart with a subtle reveal animation."""

    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(760)
        self.set_content_height(290)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.points: list[tuple[str, float]] = []
        self.value_suffix = ""
        self.progress = 1.0

    def set_points(self, points: list[tuple[str, float]], value_suffix: str = "") -> None:
        self.points = [p for p in points if math.isfinite(p[1])]
        self.value_suffix = value_suffix
        self.progress = 0.0 if self.points else 1.0
        self.queue_draw()
        if self.points:
            GLib.timeout_add(16, self._animate)

    def _animate(self) -> bool:
        self.progress = min(1.0, self.progress + 0.055)
        self.queue_draw()
        return self.progress < 1.0

    def _draw(self, _area: Gtk.DrawingArea, cr, width: int, height: int, _data=None) -> None:
        left, right = 58.0, max(59.0, width - 22.0)
        top, bottom = 20.0, max(21.0, height - 48.0)
        cw, ch = right - left, bottom - top
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.14)
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - ch * fraction
            cr.move_to(left, y)
            cr.line_to(right, y)
            cr.stroke()
        if not self.points:
            return
        values = [v for _, v in self.points]
        minimum, maximum = min(values), max(values)
        if math.isclose(minimum, maximum):
            pad = max(1.0, abs(maximum) * 0.08)
            minimum, maximum = minimum - pad, maximum + pad
        cr.set_font_size(10)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.75)
        for fraction in (0.0, 0.5, 1.0):
            value = minimum + (maximum - minimum) * fraction
            y = bottom - ch * fraction
            cr.move_to(4, y + 4)
            cr.show_text(f"{value:.0f}{self.value_suffix}")

        visible = max(1, int(math.ceil(len(self.points) * self.progress)))
        visible_points = self.points[:visible]
        cr.set_source_rgba(0.18, 0.52, 0.78, 0.95)
        cr.set_line_width(2.6)
        coords: list[tuple[float, float]] = []
        for index, (_label, value) in enumerate(visible_points):
            x = left if len(self.points) == 1 else left + cw * index / (len(self.points) - 1)
            y = bottom - ch * ((value - minimum) / (maximum - minimum))
            coords.append((x, y))
            if index == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()
        for x, y in coords:
            cr.arc(x, y, 3.6, 0, math.tau)
            cr.fill()
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.75)
        cr.set_font_size(10)
        for index, (label, _value) in enumerate(self.points):
            if len(self.points) > 10 and index not in (0, len(self.points) - 1):
                continue
            x = left if len(self.points) == 1 else left + cw * index / (len(self.points) - 1)
            cr.move_to(max(left, x - 20), height - 14)
            cr.show_text(label)


class MetricCard(Gtk.Box):
    """KPI card with a one-shot number animation."""

    def __init__(self, title: str, icon: str) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_margin_top(2)
        self.set_margin_bottom(2)
        self.set_margin_start(2)
        self.set_margin_end(2)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        image = Gtk.Image.new_from_icon_name(icon)
        image.add_css_class("dim-label")
        header.append(image)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("dim-label")
        header.append(label)
        header.set_margin_top(14)
        header.set_margin_start(14)
        header.set_margin_end(14)
        self.append(header)
        self.value = Gtk.Label(label="0")
        self.value.set_xalign(0)
        self.value.add_css_class("title-2")
        self.value.set_margin_start(14)
        self.value.set_margin_end(14)
        self.value.set_margin_bottom(14)
        self.append(self.value)
        self._target = 0.0

    def set_value(self, value: float, formatter=None, suffix: str = "") -> None:
        self._target = max(0.0, value)
        if formatter is None:
            formatter = lambda number: f"{number:.0f}"
        self.value.set_text(f"{formatter(0)}{suffix}")
        current = 0.0

        def tick() -> bool:
            nonlocal current
            current += max(0.5, (self._target - current) * 0.18)
            if abs(self._target - current) < 0.5:
                current = self._target
            self.value.set_text(f"{formatter(current)}{suffix}")
            return current != self._target

        GLib.timeout_add(16, tick)


class ActivityHeatmap(Gtk.DrawingArea):
    """GitHub-like yearly activity calendar using real daily practice data."""

    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(900)
        self.set_content_height(190)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.year = datetime.now().year
        self.days: dict[date, dict[str, object]] = {}
        self._cell_size = 12.0
        self._gap = 4.0
        self._left = 38.0
        self._top = 26.0
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", self._on_leave)
        self.add_controller(motion)

    def set_data(self, year: int, days: list[dict[str, object]]) -> None:
        self.year = year
        self.days = {item["date"]: item for item in days}
        self.queue_draw()

    def _calendar_start(self) -> date:
        first = date(self.year, 1, 1)
        return first - timedelta(days=first.weekday())

    def _weeks(self) -> int:
        start = self._calendar_start()
        last = date(self.year, 12, 31)
        return ((last - start).days // 7) + 1

    def _intensity(self, item: dict[str, object] | None, maximum: float) -> int:
        if not item:
            return 0
        duration = float(item["duration_seconds"])
        if maximum <= 0 or duration <= 0:
            return 1
        ratio = duration / maximum
        if ratio <= 0.25:
            return 1
        if ratio <= 0.5:
            return 2
        if ratio <= 0.75:
            return 3
        return 4

    @staticmethod
    def _rounded_rect(cr, x: float, y: float, size: float, radius: float) -> None:
        cr.new_sub_path()
        cr.arc(x + radius, y + radius, radius, math.pi, 1.5 * math.pi)
        cr.arc(x + size - radius, y + radius, radius, 1.5 * math.pi, 2 * math.pi)
        cr.arc(x + size - radius, y + size - radius, radius, 0, 0.5 * math.pi)
        cr.arc(x + radius, y + size - radius, radius, 0.5 * math.pi, math.pi)
        cr.close_path()

    def _draw(self, _area: Gtk.DrawingArea, cr, width: int, height: int, _data=None) -> None:
        weeks = self._weeks()
        usable = max(100.0, width - self._left - 12.0)
        cell = min(16.0, max(8.0, (usable - (weeks - 1) * 4.0) / weeks))
        gap = max(2.0, min(4.0, cell * 0.30))
        self._cell_size = cell
        self._gap = gap

        max_duration = max(
            (float(item["duration_seconds"]) for item in self.days.values()),
            default=0.0,
        )
        start = self._calendar_start()
        cr.set_font_size(10)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.82)
        for row, label in enumerate(WEEKDAYS):
            if row not in (0, 2, 4, 6):
                continue
            y = self._top + row * (cell + gap) + cell * 0.78
            cr.move_to(0, y)
            cr.show_text(label)

        last_month = None
        for week in range(weeks):
            week_start = start + timedelta(days=week * 7)
            if week_start.month != last_month and week_start.year == self.year:
                cr.move_to(self._left + week * (cell + gap), 12)
                cr.show_text(MONTHS[week_start.month - 1])
                last_month = week_start.month
            for row in range(7):
                day = week_start + timedelta(days=row)
                if day.year != self.year:
                    continue
                item = self.days.get(day)
                level = self._intensity(item, max_duration)
                x = self._left + week * (cell + gap)
                y = self._top + row * (cell + gap)
                self._rounded_rect(cr, x, y, cell, max(2.0, cell * 0.18))
                if level == 0:
                    cr.set_source_rgba(0.45, 0.45, 0.45, 0.18)
                else:
                    alpha = (0.24, 0.42, 0.62, 0.82)[level - 1]
                    cr.set_source_rgba(0.18, 0.52, 0.78, alpha)
                cr.fill()

        legend_y = min(height - 14.0, self._top + 7 * (cell + gap) + 18.0)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.82)
        cr.move_to(self._left, legend_y + cell * 0.78)
        cr.show_text("Daha az")
        x = self._left + 52
        for level in range(5):
            self._rounded_rect(cr, x, legend_y, cell, max(2.0, cell * 0.18))
            if level == 0:
                cr.set_source_rgba(0.45, 0.45, 0.45, 0.18)
            else:
                cr.set_source_rgba(0.18, 0.52, 0.78, (0.24, 0.42, 0.62, 0.82)[level - 1])
            cr.fill()
            x += cell + gap
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.82)
        cr.move_to(x + 4, legend_y + cell * 0.78)
        cr.show_text("Daha fazla")

    def _on_motion(self, _controller, x: float, y: float) -> None:
        week = int((x - self._left) / (self._cell_size + self._gap))
        row = int((y - self._top) / (self._cell_size + self._gap))
        if week < 0 or week >= self._weeks() or row < 0 or row >= 7:
            self.set_tooltip_text(None)
            return
        start = self._calendar_start()
        day = start + timedelta(days=week * 7 + row)
        if day.year != self.year:
            self.set_tooltip_text(None)
            return
        item = self.days.get(day)
        if not item:
            text = f"{day.day} {MONTHS[day.month - 1]} {day.year}\nÇalışma yok"
        else:
            text = (
                f"{day.day} {MONTHS[day.month - 1]} {day.year}\n"
                f"{int(item['sessions'])} çalışma · {self._duration_text(float(item['duration_seconds']))}\n"
                f"Ortalama hız: Dakikada {float(item['average_speed']):.0f} kelime · "
                f"Doğruluk: %{float(item['accuracy_percent']):.0f}"
            )
        self.set_tooltip_text(text)

    def _on_leave(self, _controller) -> None:
        self.set_tooltip_text(None)

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


class StatisticsPanel(Gtk.Box):
    """Adaptive statistics dashboard backed entirely by real SQLite records."""

    PERIODS = ("Günlük", "Haftalık", "Aylık", "Yıllık", "Tümü")

    def __init__(self, database: Database) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.db = database
        self.selected_period = "Haftalık"
        self.activity_year = datetime.now().year
        self._build()
        self.refresh()

    @staticmethod
    def _revealed(child: Gtk.Widget, delay: int) -> Gtk.Revealer:
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        revealer.set_transition_duration(220)
        revealer.set_reveal_child(False)
        revealer.set_child(child)
        GLib.timeout_add(delay, lambda: (revealer.set_reveal_child(True), GLib.SOURCE_REMOVE)[1])
        return revealer

    @staticmethod
    def _icon_label(icon: str, title: str, subtitle: str | None = None) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        image = Gtk.Image.new_from_icon_name(icon)
        image.add_css_class("dim-label")
        row.append(image)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("title-2")
        row.append(label)
        box.append(row)
        if subtitle:
            detail = Gtk.Label(label=subtitle)
            detail.set_xalign(0)
            detail.set_wrap(True)
            detail.add_css_class("dim-label")
            box.append(detail)
        return box

    def _build(self) -> None:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22)
        content.set_hexpand(True)
        content.set_margin_top(28)
        content.set_margin_bottom(40)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scrolled.set_child(content)

        content.append(self._revealed(self._make_header(), 40))
        content.append(self._revealed(self._make_period_selector(), 80))
        content.append(self._revealed(self._make_metrics(), 120))
        content.append(self._revealed(self._make_speed_section(), 160))
        content.append(self._revealed(self._make_accuracy_section(), 200))
        content.append(self._revealed(self._make_activity_section(), 240))
        content.append(self._revealed(self._make_records_section(), 280))
        content.append(self._revealed(self._make_progress_section(), 320))
        content.append(self._revealed(self._make_history_section(), 360))

    def _make_header(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.append(self._icon_label("utilities-system-monitor-symbolic", "İstatistikler"))
        subtitle = Gtk.Label(label="Yazma gelişimini tek bakışta takip et.")
        subtitle.set_xalign(0)
        subtitle.set_wrap(True)
        subtitle.add_css_class("dim-label")
        box.append(subtitle)
        return box

    def _make_period_selector(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        section.append(self._icon_label("view-calendar-symbolic", "Dönem"))
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        controls.add_css_class("linked")
        self.period_buttons: list[Gtk.ToggleButton] = []
        previous = None
        for period in self.PERIODS:
            button = Gtk.ToggleButton(label=period)
            button.set_hexpand(True)
            button.set_active(period == self.selected_period)
            if previous is not None:
                button.set_group(previous)
            button.connect("toggled", self._on_period_toggled, period)
            controls.append(button)
            self.period_buttons.append(button)
            previous = button
        section.append(controls)
        return section

    def _make_metrics(self) -> Gtk.Box:
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        self.metric_cards = (
            MetricCard("Ortalama hız", "speedometer-symbolic"),
            MetricCard("Doğruluk", "emblem-ok-symbolic"),
            MetricCard("Çalışma süresi", "preferences-system-time-symbolic"),
            MetricCard("Çalışma sayısı", "view-list-symbolic"),
        )
        for index, card in enumerate(self.metric_cards):
            grid.attach(card, index, 0, 1, 1)
        return grid

    def _make_speed_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label("speedometer-symbolic", "Yazma hızı", "Çalışmalarındaki hız değişimi"))
        frame = Gtk.Frame()
        frame.add_css_class("card")
        chart_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        chart_box.set_margin_top(12)
        chart_box.set_margin_bottom(12)
        chart_box.set_margin_start(12)
        chart_box.set_margin_end(12)
        self.chart = ProgressChart()
        chart_box.append(self.chart)
        self.chart_empty = Gtk.Label(label="Tamamlanmış çalışmalar burada grafik olarak görünecek.")
        self.chart_empty.add_css_class("dim-label")
        self.chart_empty.set_margin_top(12)
        self.chart_empty.set_margin_bottom(12)
        chart_box.append(self.chart_empty)
        frame.set_child(chart_box)
        section.append(frame)
        return section

    def _make_accuracy_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label("emblem-ok-symbolic", "Doğruluk", "Doğru ve yanlış kelimeleri birlikte gör"))
        frame = Gtk.Frame()
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)
        self.accuracy_value = Gtk.Label(label="%0")
        self.accuracy_value.add_css_class("title-1")
        self.accuracy_value.set_xalign(0)
        box.append(self.accuracy_value)
        self.accuracy_bar = Gtk.ProgressBar()
        self.accuracy_bar.set_show_text(False)
        self.accuracy_bar.set_hexpand(True)
        box.append(self.accuracy_bar)
        split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        correct = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        correct.append(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
        self.correct_label = Gtk.Label(label="Doğru: 0")
        self.correct_label.set_xalign(0)
        correct.append(self.correct_label)
        wrong = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        wrong.append(Gtk.Image.new_from_icon_name("dialog-warning-symbolic"))
        self.wrong_label = Gtk.Label(label="Yanlış: 0")
        self.wrong_label.set_xalign(0)
        wrong.append(self.wrong_label)
        split.append(correct)
        split.append(wrong)
        box.append(split)
        frame.set_child(box)
        section.append(frame)
        return section

    def _make_activity_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label(
            "x-office-calendar-symbolic",
            "Çalışma takvimi",
            "Yıl boyunca yaptığın pratikleri GitHub tarzı katkı görünümünde takip et.",
        ))
        frame = Gtk.Frame()
        frame.add_css_class("card")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(14)
        outer.set_margin_bottom(14)
        outer.set_margin_start(14)
        outer.set_margin_end(14)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        year_icon = Gtk.Image.new_from_icon_name("view-calendar-symbolic")
        year_icon.add_css_class("dim-label")
        controls.append(year_icon)
        year_label = Gtk.Label(label="Yıl")
        year_label.set_xalign(0)
        year_label.add_css_class("dim-label")
        controls.append(year_label)
        self.activity_year_dropdown = Gtk.DropDown()
        self.activity_year_dropdown.set_hexpand(False)
        self.activity_year_dropdown.connect("notify::selected", self._on_activity_year_changed)
        controls.append(self.activity_year_dropdown)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        controls.append(spacer)
        outer.append(controls)

        self.activity_summary = Gtk.Label(label="Henüz çalışma yok")
        self.activity_summary.set_xalign(0)
        self.activity_summary.add_css_class("dim-label")
        outer.append(self.activity_summary)
        self.activity_heatmap = ActivityHeatmap()
        outer.append(self.activity_heatmap)
        frame.set_child(outer)
        section.append(frame)
        return section

    def _make_records_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label("starred-symbolic", "Kişisel rekorlar", "Seçili dönemdeki en yüksek değerlerin"))
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        titles = ("En yüksek hız", "En yüksek doğruluk", "En uzun çalışma", "En yoğun gün")
        icons = ("speedometer-symbolic", "emblem-ok-symbolic", "preferences-system-time-symbolic", "x-office-calendar-symbolic")
        self.record_values: list[Gtk.Label] = []
        for i, (title, icon) in enumerate(zip(titles, icons)):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.add_css_class("card")
            card.set_hexpand(True)
            card.set_margin_top(2)
            card.set_margin_bottom(2)
            card.set_margin_start(2)
            card.set_margin_end(2)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
            row.set_margin_top(12)
            row.set_margin_start(12)
            row.set_margin_end(12)
            row.append(Gtk.Image.new_from_icon_name(icon))
            name = Gtk.Label(label=title)
            name.set_xalign(0)
            name.set_wrap(True)
            name.add_css_class("dim-label")
            row.append(name)
            card.append(row)
            value = Gtk.Label(label="—")
            value.set_xalign(0)
            value.set_wrap(True)
            value.add_css_class("heading")
            value.set_margin_start(12)
            value.set_margin_bottom(12)
            card.append(value)
            self.record_values.append(value)
            grid.attach(card, i, 0, 1, 1)
        section.append(grid)
        return section

    def _make_progress_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label("go-next-symbolic", "Gelişim", "İlk ve son çalışmaların arasındaki değişim"))
        group = Adw.PreferencesGroup()
        self.progress_speed = Adw.ActionRow()
        self.progress_speed.set_title("Yazma hızı")
        self.progress_speed.set_subtitle("Yeterli veri olduğunda gösterilir")
        self.progress_speed.add_prefix(Gtk.Image.new_from_icon_name("speedometer-symbolic"))
        group.add(self.progress_speed)
        self.progress_accuracy = Adw.ActionRow()
        self.progress_accuracy.set_title("Doğruluk")
        self.progress_accuracy.set_subtitle("Yeterli veri olduğunda gösterilir")
        self.progress_accuracy.add_prefix(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
        group.add(self.progress_accuracy)
        section.append(group)
        return section

    def _make_history_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._icon_label("view-list-symbolic", "Son çalışmalar", "Tamamlanan çalışmaların ayrıntıları"))
        frame = Gtk.Frame()
        frame.add_css_class("card")
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.history_empty = Gtk.Label(label="Henüz tamamlanmış çalışma yok")
        self.history_empty.add_css_class("dim-label")
        self.history_empty.set_margin_top(18)
        self.history_empty.set_margin_bottom(18)
        self.history_empty.set_margin_start(16)
        self.history_empty.set_margin_end(16)
        self.history_box.append(self.history_empty)
        frame.set_child(self.history_box)
        section.append(frame)
        return section

    def _on_period_toggled(self, button: Gtk.ToggleButton, period: str) -> None:
        if button.get_active():
            self.selected_period = period
            self.refresh()

    def _on_activity_year_changed(self, dropdown: Gtk.DropDown, _pspec) -> None:
        model = dropdown.get_model()
        if model is None or dropdown.get_selected() == Gtk.INVALID_LIST_POSITION:
            return
        item = model.get_item(dropdown.get_selected())
        if item is None:
            return
        try:
            self.activity_year = int(item.get_string())
        except ValueError:
            return
        self._refresh_activity()

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

    def _refresh_activity_years(self) -> None:
        years = self.db.practice_activity_years()
        current = datetime.now().year
        if current not in years:
            years.insert(0, current)
        years = sorted(set(years), reverse=True)
        if self.activity_year not in years:
            self.activity_year = years[0]
        model = Gtk.StringList.new([str(year) for year in years])
        self.activity_year_dropdown.set_model(model)
        self.activity_year_dropdown.set_selected(years.index(self.activity_year))

    def _refresh_activity(self) -> None:
        data = self.db.practice_activity(self.activity_year)
        self.activity_heatmap.set_data(self.activity_year, data)
        if not data:
            self.activity_summary.set_text(f"{self.activity_year}: Henüz çalışma yapılmadı.")
            return
        total_sessions = sum(int(item["sessions"]) for item in data)
        total_duration = sum(float(item["duration_seconds"]) for item in data)
        self.activity_summary.set_text(
            f"{self.activity_year}: {len(data)} aktif gün · {total_sessions} çalışma · {self._duration_text(total_duration)} toplam süre"
        )

    def _set_records(self, history: list[dict[str, object]]) -> None:
        if not history:
            for label in self.record_values:
                label.set_text("—")
            return
        fastest = max(history, key=lambda x: float(x["words_per_minute"]))
        accurate = max(history, key=lambda x: float(x["accuracy_percent"]))
        longest = max(history, key=lambda x: float(x["duration_seconds"]))
        by_day: dict[object, float] = {}
        for item in history:
            day = item["completed_at"].date()
            by_day[day] = by_day.get(day, 0.0) + float(item["duration_seconds"])
        busiest = max(by_day.items(), key=lambda x: x[1])
        self.record_values[0].set_text(f"Dakikada {float(fastest['words_per_minute']):.0f} kelime")
        self.record_values[1].set_text(f"%{float(accurate['accuracy_percent']):.0f}")
        self.record_values[2].set_text(self._duration_text(float(longest["duration_seconds"])))
        self.record_values[3].set_text(f"{busiest[0].day} {MONTHS[busiest[0].month - 1]}")

    def _set_progress(self, history: list[dict[str, object]]) -> None:
        if len(history) < 2:
            self.progress_speed.set_subtitle("En az iki çalışma olduğunda karşılaştırma gösterilir")
            self.progress_accuracy.set_subtitle("En az iki çalışma olduğunda karşılaştırma gösterilir")
            return
        ordered = sorted(history, key=lambda x: x["completed_at"])
        first, latest = ordered[0], ordered[-1]
        speed_delta = float(latest["words_per_minute"]) - float(first["words_per_minute"])
        accuracy_delta = float(latest["accuracy_percent"]) - float(first["accuracy_percent"])
        speed_sign = "+" if speed_delta >= 0 else ""
        accuracy_sign = "+" if accuracy_delta >= 0 else ""
        self.progress_speed.set_subtitle(
            f"İlk: Dakikada {float(first['words_per_minute']):.0f} kelime  →  "
            f"Son: Dakikada {float(latest['words_per_minute']):.0f} kelime  ({speed_sign}{speed_delta:.0f})"
        )
        self.progress_accuracy.set_subtitle(
            f"İlk: %{float(first['accuracy_percent']):.0f}  →  "
            f"Son: %{float(latest['accuracy_percent']):.0f}  ({accuracy_sign}{accuracy_delta:.0f} puan)"
        )

    def _set_history(self, history: list[dict[str, object]]) -> None:
        self._clear_box(self.history_box)
        if not history:
            self.history_box.append(self.history_empty)
            return
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(16)
        header.set_margin_end(16)
        for icon, title in (
            ("view-calendar-symbolic", "Tarih"),
            ("folder-documents-symbolic", "Ders"),
            ("preferences-system-time-symbolic", "Süre"),
            ("input-keyboard-symbolic", "Sonuç"),
            ("emblem-ok-symbolic", "Doğruluk"),
            ("speedometer-symbolic", "Hız"),
        ):
            cell = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            cell.set_hexpand(True)
            cell.append(Gtk.Image.new_from_icon_name(icon))
            label = Gtk.Label(label=title)
            label.set_xalign(0)
            label.add_css_class("dim-label")
            cell.append(label)
            header.append(cell)
        self.history_box.append(header)
        self.history_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        for item in history:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.set_margin_top(9)
            row.set_margin_bottom(9)
            row.set_margin_start(16)
            row.set_margin_end(16)
            values = (
                self._date_text(item["completed_at"]),
                str(item["lesson_title"] or "Ders"),
                self._duration_text(float(item["duration_seconds"])),
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
            self.history_box.append(row)

    def refresh(self) -> None:
        stats = self.db.practice_statistics(self.selected_period)
        practices = int(stats["practices"])
        duration = float(stats["duration_seconds"])
        accuracy = float(stats["accuracy_percent"])
        speed_points = list(stats["speed_points"])
        history = list(stats["history"])
        average_speed = sum(float(v) for _label, v in speed_points) / len(speed_points) if speed_points else 0.0

        self.metric_cards[0].set_value(average_speed, lambda n: f"{n:.0f}", " kelime/dk")
        self.metric_cards[1].set_value(accuracy, lambda n: f"%{n:.0f}")
        self.metric_cards[2].set_value(duration / 60.0, lambda n: self._duration_text(n * 60))
        self.metric_cards[3].set_value(practices)
        self.chart.set_points(speed_points)
        self.chart_empty.set_visible(not bool(speed_points))
        self.accuracy_value.set_text(f"%{accuracy:.0f}")
        self.accuracy_bar.set_fraction(max(0.0, min(1.0, accuracy / 100.0)))
        self.correct_label.set_text(f"Doğru: {int(stats['correct_words'])}")
        self.wrong_label.set_text(f"Yanlış: {int(stats['wrong_words'])}")
        self._refresh_activity_years()
        self._refresh_activity()
        self._set_records(history)
        self._set_progress(history)
        self._set_history(history)
