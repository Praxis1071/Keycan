"""Statistics page UI for Keycan.

Stage 2 defines the presentation and navigation surface only. Real practice
records are intentionally supplied by the data layer in Stage 3.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class StatCard(Gtk.Box):
    """Small summary card with a user-facing label and value."""

    def __init__(self, title: str, value: str = "—") -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_margin_top(2)
        self.set_margin_bottom(2)
        self.set_margin_start(2)
        self.set_margin_end(2)

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0)
        title_label.add_css_class("dim-label")
        self.append(title_label)

        self.value_label = Gtk.Label(label=value)
        self.value_label.set_xalign(0)
        self.value_label.add_css_class("title-3")
        self.append(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.set_text(value)


class StatisticsPanel(Gtk.Box):
    """Responsive Stage 2 statistics surface, independent of SQLite queries."""

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

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.set_margin_top(24)
        content.set_margin_bottom(28)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_hexpand(True)
        scrolled.set_child(content)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label="İstatistikler")
        title.set_xalign(0)
        title.add_css_class("title-1")
        header.append(title)
        description = Gtk.Label(
            label="Yazma çalışmalarındaki ilerlemeni zaman içinde takip et."
        )
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        header.append(description)
        content.append(header)

        cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        cards.set_hexpand(True)
        self.summary_cards = [
            StatCard("Toplam çalışma"),
            StatCard("Toplam süre"),
            StatCard("Toplam kelime"),
            StatCard("Ortalama doğruluk"),
        ]
        for card in self.summary_cards:
            cards.append(card)
        content.append(cards)

        period_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        period_label = Gtk.Label(label="Zaman aralığı")
        period_label.set_xalign(0)
        period_label.set_valign(Gtk.Align.CENTER)
        period_row.append(period_label)

        self.period_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.period_buttons.add_css_class("linked")
        self._period_group = None
        for index, period in enumerate(self.PERIODS):
            button = Gtk.ToggleButton(label=period)
            button.set_active(index == 1)
            button.connect("toggled", self._on_period_toggled, index)
            self.period_buttons.append(button)
            if index == 1:
                self._active_period = button
        period_row.append(self.period_buttons)
        content.append(period_row)

        graph_frame = Gtk.Frame()
        graph_frame.set_hexpand(True)
        graph_frame.set_vexpand(True)
        graph_frame.set_size_request(-1, 250)
        graph_frame.add_css_class("card")
        graph_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        graph_content.set_margin_top(18)
        graph_content.set_margin_bottom(18)
        graph_content.set_margin_start(18)
        graph_content.set_margin_end(18)

        graph_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        graph_title = Gtk.Label(label="Yazma gelişimi")
        graph_title.set_xalign(0)
        graph_title.add_css_class("title-3")
        graph_header.append(graph_title)
        graph_header.append(Gtk.Label(label="·"))
        graph_metric = Gtk.Label(label="Dakikada kelime")
        graph_metric.add_css_class("dim-label")
        graph_header.append(graph_metric)
        graph_content.append(graph_header)

        self.graph_placeholder = Gtk.Label(
            label="Henüz tamamlanmış bir çalışma yok.\nİlk çalışmanı tamamladığında ilerlemen burada görünecek."
        )
        self.graph_placeholder.set_justify(Gtk.Justification.CENTER)
        self.graph_placeholder.set_wrap(True)
        self.graph_placeholder.set_hexpand(True)
        self.graph_placeholder.set_vexpand(True)
        self.graph_placeholder.add_css_class("dim-label")
        graph_content.append(self.graph_placeholder)
        graph_frame.set_child(graph_content)
        content.append(graph_frame)

        analysis = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        analysis.set_hexpand(True)

        accuracy_frame = self._make_analysis_card(
            "Doğruluk analizi",
            "Henüz veri yok",
            "Doğru ve yanlış kelimeler, çalışmalar tamamlandıkça burada özetlenecek.",
        )
        analysis.append(accuracy_frame)

        result_frame = self._make_analysis_card(
            "Çalışma özeti",
            "Henüz veri yok",
            "Tamamlanan çalışmaların toplam ve ortalama sonuçları burada gösterilecek.",
        )
        analysis.append(result_frame)
        content.append(analysis)

        history_frame = Gtk.Frame()
        history_frame.set_hexpand(True)
        history_frame.add_css_class("card")
        history_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        history_content.set_margin_top(18)
        history_content.set_margin_bottom(18)
        history_content.set_margin_start(18)
        history_content.set_margin_end(18)

        history_title = Gtk.Label(label="Çalışmalarım")
        history_title.set_xalign(0)
        history_title.add_css_class("title-3")
        history_content.append(history_title)

        self.history_placeholder = Gtk.Label(
            label="Henüz tamamlanmış bir çalışma yok.\nİlk çalışmanı tamamladığında geçmiş çalışmaların burada görünecek."
        )
        self.history_placeholder.set_xalign(0)
        self.history_placeholder.set_wrap(True)
        self.history_placeholder.add_css_class("dim-label")
        history_content.append(self.history_placeholder)

        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        columns.set_hexpand(True)
        for column in ("Tarih", "Ders", "Süre", "Sonuç", "Doğruluk", "Hız"):
            label = Gtk.Label(label=column)
            label.set_xalign(0)
            label.set_hexpand(True)
            label.add_css_class("dim-label")
            columns.append(label)
        history_content.append(columns)
        history_frame.set_child(history_content)
        content.append(history_frame)

        self._apply_responsive_behavior()

    def _make_analysis_card(self, title: str, value: str, description: str) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.set_hexpand(True)
        frame.add_css_class("card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0)
        title_label.add_css_class("title-3")
        box.append(title_label)
        value_label = Gtk.Label(label=value)
        value_label.set_xalign(0)
        box.append(value_label)
        detail = Gtk.Label(label=description)
        detail.set_xalign(0)
        detail.set_wrap(True)
        detail.add_css_class("dim-label")
        box.append(detail)
        frame.set_child(box)
        return frame

    def _on_period_toggled(self, button: Gtk.ToggleButton, index: int) -> None:
        if not button.get_active():
            return
        for child in self.period_buttons.observe_children():
            if child is not button and isinstance(child, Gtk.ToggleButton):
                child.set_active(False)
        self._active_period = button
        # Real period-specific data is intentionally wired in Stage 3.
        self.graph_placeholder.set_text(
            "Henüz tamamlanmış bir çalışma yok.\n"
            "İlk çalışmanı tamamladığında bu görünümde ilerlemen gösterilecek."
        )

    def _apply_responsive_behavior(self) -> None:
        # The compact view keeps cards usable without requiring a separate
        # window. Gtk.Box naturally clips/reflows through the scrolled page;
        # the main window's minimum size protects the typing workspace.
        self.set_size_request(0, 0)
