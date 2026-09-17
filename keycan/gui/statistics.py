"""Simple, progress-focused statistics surface for Keycan Stage 2.

Stage 2 owns presentation and interaction only. Real SQLite records are wired
in Stage 3; this screen is deliberately designed so no fake statistics are
shown while the data source is empty.
"""

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, GLib, Gtk


class ProgressChart(Gtk.DrawingArea):
    """Lightweight chart surface ready for real Stage 3 data."""

    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(720)
        self.set_content_height(250)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_draw_func(self._draw)

    @staticmethod
    def _draw(_area: Gtk.DrawingArea, cr, width: int, height: int, _data) -> None:
        left = 42
        right = max(left + 1, width - 18)
        top = 18
        bottom = max(top + 1, height - 34)

        # The empty chart keeps the same geometry that Stage 3 will use for
        # real points. No fabricated measurements are drawn.
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.22)
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - (bottom - top) * fraction
            cr.move_to(left, y)
            cr.line_to(right, y)
            cr.stroke()
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.45)
        cr.move_to(left, top)
        cr.line_to(left, bottom)
        cr.line_to(right, bottom)
        cr.stroke()


class StatisticsPanel(Gtk.Box):
    """Responsive, understandable progress page independent of SQLite."""

    PERIODS = ("Günlük", "Haftalık", "Aylık")

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)
        self.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(1100)
        clamp.set_tightening_threshold(760)
        scrolled.set_child(clamp)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_hexpand(True)
        clamp.set_child(content)

        self._add_revealed(content, self._make_header(), 60)
        self._add_revealed(content, self._make_overview(), 120)
        self._add_revealed(content, self._make_progress_section(), 180)
        self._add_revealed(content, self._make_accuracy_section(), 240)
        self._add_revealed(content, self._make_history_section(), 300)

    def _add_revealed(self, parent: Gtk.Box, child: Gtk.Widget, delay_ms: int) -> None:
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        revealer.set_transition_duration(220)
        revealer.set_reveal_child(False)
        revealer.set_child(child)
        parent.append(revealer)
        GLib.timeout_add(delay_ms, self._reveal, revealer)

    @staticmethod
    def _reveal(revealer: Gtk.Revealer) -> bool:
        revealer.set_reveal_child(True)
        return GLib.SOURCE_REMOVE

    @staticmethod
    def _section_title(title: str, description: str | None = None) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("title-3")
        box.append(label)
        if description:
            detail = Gtk.Label(label=description)
            detail.set_xalign(0)
            detail.set_wrap(True)
            detail.add_css_class("dim-label")
            box.append(detail)
        return box

    def _make_header(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label="İstatistikler")
        title.set_xalign(0)
        title.add_css_class("title-1")
        box.append(title)
        description = Gtk.Label(label="Yazma gelişimini tek bakışta takip et.")
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        box.append(description)
        return box

    def _make_overview(self) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.append(self._section_title("Genel durum"))

        metrics = Gtk.FlowBox()
        metrics.set_selection_mode(Gtk.SelectionMode.NONE)
        metrics.set_row_spacing(10)
        metrics.set_column_spacing(10)
        metrics.set_min_children_per_line(1)
        metrics.set_max_children_per_line(4)
        metrics.set_homogeneous(True)
        metrics.set_hexpand(True)
        for title in ("Çalışma", "Toplam süre", "Kelime", "Doğruluk"):
            metrics.append(self._make_metric(title))
        box.append(metrics)
        frame.set_child(box)
        return frame

    @staticmethod
    def _make_metric(title: str) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box.add_css_class("card")
        box.set_margin_top(1)
        box.set_margin_bottom(1)
        box.set_margin_start(1)
        box.set_margin_end(1)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.add_css_class("dim-label")
        box.append(label)
        value = Gtk.Label(label="—")
        value.set_xalign(0)
        value.add_css_class("title-3")
        box.append(value)
        return box

    def _make_progress_section(self) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        heading.append(self._section_title("Yazma hızın", "Zaman içindeki gelişimin"))
        period_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        period_box.add_css_class("linked")
        self.period_buttons: list[Gtk.ToggleButton] = []
        for index, period in enumerate(self.PERIODS):
            button = Gtk.ToggleButton(label=period)
            button.set_active(index == 1)
            button.connect("toggled", self._on_period_toggled, index)
            self.period_buttons.append(button)
            period_box.append(button)
        heading.append(period_box)
        box.append(heading)

        self.chart = ProgressChart()
        box.append(self.chart)

        empty = Gtk.Label(
            label="Henüz tamamlanmış bir çalışma yok.\nİlk çalışmanı tamamladığında hızındaki değişim burada görünecek."
        )
        empty.set_justify(Gtk.Justification.CENTER)
        empty.set_wrap(True)
        empty.set_margin_top(-120)
        empty.set_margin_bottom(80)
        empty.add_css_class("dim-label")
        box.append(empty)
        frame.set_child(box)
        return frame

    def _make_accuracy_section(self) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.append(self._section_title("Doğruluk", "Doğru ve yanlış kelimelerin dengesi"))

        message = Gtk.Label(
            label="Çalışmalar tamamlandıkça doğru kelimeler, yanlış kelimeler ve doğruluk yüzdesi burada gösterilecek."
        )
        message.set_xalign(0)
        message.set_wrap(True)
        message.add_css_class("dim-label")
        box.append(message)
        frame.set_child(box)
        return frame

    def _make_history_section(self) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.append(self._section_title("Son çalışmaların", "En yeni çalışmalar burada listelenecek."))

        table = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Gtk.Grid()
        header.set_column_spacing(18)
        header.set_row_spacing(8)
        columns = ("Tarih", "Ders", "Süre", "Sonuç", "Doğruluk", "Hız")
        for column, title in enumerate(columns):
            label = Gtk.Label(label=title)
            label.set_xalign(0)
            label.add_css_class("dim-label")
            label.set_hexpand(True)
            header.attach(label, column, 0, 1, 1)
        table.append(header)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        table.append(separator)

        empty = Gtk.Label(label="Henüz tamamlanmış bir çalışma yok.")
        empty.set_xalign(0)
        empty.set_margin_top(8)
        empty.set_margin_bottom(8)
        empty.add_css_class("dim-label")
        table.append(empty)
        box.append(table)
        frame.set_child(box)
        return frame

    def _on_period_toggled(self, button: Gtk.ToggleButton, _index: int) -> None:
        if not button.get_active():
            return
        for other in self.period_buttons:
            if other is not button:
                other.set_active(False)
        # Stage 3 will replace the empty chart with period-specific data.
