"""Polished, SQLite-backed practice statistics for Keycan."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
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
    """Compact KPI card with a one-shot number animation."""

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
        self._suffix = ""

    def set_value(self, value: float, formatter=None, suffix: str = "") -> None:
        self._target = max(0.0, value)
        self._suffix = suffix
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


class StatisticsPanel(Gtk.Box):
    """Adaptive statistics dashboard backed entirely by real SQLite records."""

    PERIODS = ("Günlük", "Haftalık", "Aylık", "Yıllık", "Tümü")

    def __init__(self, database: Database) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.db = database
        self.selected_period = "Haftalık"
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

    def _build(self) -> None:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        # Statistics should follow the available content width just like the
        # workspace and settings views. Only the content margins provide the
        # visual breathing room; there is no artificial centered max width.
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

    @staticmethod
    def _heading(title: str, subtitle: str | None = None, icon: str | None = None) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        if icon:
            image = Gtk.Image.new_from_icon_name(icon)
            image.add_css_class("dim-label")
            title_row.append(image)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("title-2")
        title_row.append(label)
        box.append(title_row)
        if subtitle:
            detail = Gtk.Label(label=subtitle)
            detail.set_xalign(0)
            detail.set_wrap(True)
            detail.add_css_class("dim-label")
            box.append(detail)
        return box

    def _make_header(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        image = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic")
        image.add_css_class("dim-label")
        title_row.append(image)
        title = Gtk.Label(label="İstatistikler")
        title.set_xalign(0)
        title.add_css_class("title-1")
        title_row.append(title)
        box.append(title_row)
        subtitle = Gtk.Label(label="Yazma gelişimini tek bakışta takip et.")
        subtitle.set_xalign(0)
        subtitle.set_wrap(True)
        subtitle.add_css_class("dim-label")
        box.append(subtitle)
        return box

    def _make_period_selector(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        section.append(self._heading("Dönem", icon="view-calendar-symbolic"))
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
        section.append(self._heading("Yazma hızı", "Çalışmalarındaki hız değişimi", "speedometer-symbolic"))
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
        section.append(self._heading("Doğruluk", "Doğru ve yanlış kelimeleri birlikte gör", "emblem-ok-symbolic"))
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
        correct_image = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        correct_image.add_css_class("dim-label")
        correct.append(correct_image)
        self.correct_label = Gtk.Label(label="Doğru: 0")
        self.correct_label.set_xalign(0)
        correct.append(self.correct_label)
        wrong = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        wrong_image = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        wrong_image.add_css_class("dim-label")
        wrong.append(wrong_image)
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
        section.append(self._heading("Çalışma takvimi", "Hangi günlerde pratik yaptığını gör", "x-office-calendar-symbolic"))
        frame = Gtk.Frame()
        frame.add_css_class("card")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_top(14)
        outer.set_margin_bottom(14)
        outer.set_margin_start(14)
        outer.set_margin_end(14)
        self.activity_summary = Gtk.Label(label="Henüz çalışma yok")
        self.activity_summary.set_xalign(0)
        self.activity_summary.add_css_class("dim-label")
        outer.append(self.activity_summary)
        self.activity_grid = Gtk.Grid()
        self.activity_grid.set_row_spacing(5)
        self.activity_grid.set_column_spacing(5)
        outer.append(self.activity_grid)
        frame.set_child(outer)
        section.append(frame)
        return section

    def _make_records_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Kişisel rekorlar", "Seçili dönemdeki en yüksek değerlerin", "starred-symbolic"))
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        titles = ("En yüksek hız", "En yüksek doğruluk", "En uzun çalışma", "En yoğun gün")
        icons = ("speedometer-symbolic", "emblem-ok-symbolic", "preferences-system-time-symbolic", "x-office-calendar-symbolic")
        self.record_values: list[Gtk.Label] = []
        for i, (title, icon) in enumerate(zip(titles, icons)):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.add_css_class("card")
            card.set_margin_top(2)
            card.set_margin_bottom(2)
            card.set_margin_start(2)
            card.set_margin_end(2)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
            row.set_margin_top(12)
            row.set_margin_start(12)
            row.set_margin_end(12)
            image = Gtk.Image.new_from_icon_name(icon)
            image.add_css_class("dim-label")
            row.append(image)
            name = Gtk.Label(label=title)
            name.set_xalign(0)
            name.add_css_class("dim-label")
            row.append(name)
            card.append(row)
            value = Gtk.Label(label="—")
            value.set_xalign(0)
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
        section.append(self._heading("Gelişim", "İlk ve son çalışmaların arasındaki değişim", "go-next-symbolic"))
        group = Adw.PreferencesGroup()
        self.progress_speed = Adw.ActionRow()
        self.progress_speed.set_title("Yazma hızı")
        self.progress_speed.set_subtitle("Yeterli veri olduğunda gösterilir")
        speed_icon = Gtk.Image.new_from_icon_name("speedometer-symbolic")
        speed_icon.add_css_class("dim-label")
        self.progress_speed.add_prefix(speed_icon)
        group.add(self.progress_speed)
        self.progress_accuracy = Adw.ActionRow()
        self.progress_accuracy.set_title("Doğruluk")
        self.progress_accuracy.set_subtitle("Yeterli veri olduğunda gösterilir")
        accuracy_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        accuracy_icon.add_css_class("dim-label")
        self.progress_accuracy.add_prefix(accuracy_icon)
        group.add(self.progress_accuracy)
        section.append(group)
        return section

    def _make_history_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        section.append(self._heading("Son çalışmalar", "Tamamlanan çalışmaların ayrıntıları", "view-list-symbolic"))
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

    def _set_activity(self, history: list[dict[str, object]]) -> None:
        self._clear_box(self.activity_grid)
        if not history:
            self.activity_summary.set_text("Henüz çalışma yapılmadı.")
            return
        daily: dict[object, float] = {}
        for item in history:
            day = item["completed_at"].date()
            daily[day] = daily.get(day, 0.0) + float(item["duration_seconds"])
        end = datetime.now().astimezone().date()
        start = end - timedelta(days=34)
        self.activity_summary.set_text(f"Son 35 gün: {len(daily)} aktif gün")
        for col in range(5):
            label = Gtk.Label(label=WEEKDAYS[col])
            label.add_css_class("dim-label")
            self.activity_grid.attach(label, col + 1, 0, 1, 1)
        for index in range(35):
            day = start + timedelta(days=index)
            value = daily.get(day, 0.0)
            cell = Gtk.Label(label=" ")
            cell.set_size_request(22, 22)
            cell.set_tooltip_text(f"{day.day} {MONTHS[day.month - 1]}: {self._duration_text(value)}")
            cell.add_css_class("card")
            if value > 0:
                cell.add_css_class("accent-bg")
            row = index // 5 + 1
            col = index % 5 + 1
            self.activity_grid.attach(cell, col, row, 1, 1)

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
        for title in ("Tarih", "Ders", "Süre", "Sonuç", "Doğruluk", "Hız"):
            label = Gtk.Label(label=title)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.add_css_class("dim-label")
            header.append(label)
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
        words = int(stats["total_words"])
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
        self._set_activity(history)
        self._set_records(history)
        self._set_progress(history)
        self._set_history(history)
