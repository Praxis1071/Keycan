#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

import keycan.app as keycan_app
import keycan.window as keycan_window
from keycan.app import main
from keycan.gui.search import SourceSearchDropdown
from keycan.gui.settings import SettingsPanel
from keycan.gui.statistics import StatisticsPanel


class ConfiguredKeycanWindow(keycan_window.KeycanWindow):
    def __init__(self, app: Adw.Application, database_path):
        super().__init__(app, database_path)
        self.maximize()
        self.text_size = 22
        self.size_spin.set_value(22)
        self.workspace.set_text_size(self.text_size)

    def _build_ui(self) -> None:
        super()._build_ui()

        old_dropdown = self.source_dropdown
        parent = old_dropdown.get_parent()
        previous = old_dropdown.get_prev_sibling() if parent is not None else None
        self.source_dropdown = SourceSearchDropdown()
        self.source_dropdown.on_selected_changed = self._on_source_changed
        self.source_dropdown.set_hexpand(True)
        self.source_dropdown.set_halign(Gtk.Align.FILL)

        if parent is not None:
            old_dropdown.unparent()
            if previous is not None:
                self.source_dropdown.insert_after(parent, previous)
            else:
                parent.append(self.source_dropdown)

        self._install_sidebar_navigation()

    def _install_sidebar_navigation(self) -> None:
        toolbar = self.get_content()
        if not isinstance(toolbar, Adw.ToolbarView):
            return
        root = toolbar.get_content()
        if not isinstance(root, Gtk.Box):
            return

        # The sidebar is always collapsed so it overlays the main content
        # instead of changing the typing workspace geometry.
        split_view = Adw.OverlaySplitView()
        split_view.set_collapsed(True)
        split_view.set_sidebar_position(Gtk.PackType.START)
        split_view.set_min_sidebar_width(260)
        split_view.set_max_sidebar_width(340)
        split_view.set_sidebar_width_fraction(0.25)
        split_view.set_show_sidebar(False)
        split_view.set_enable_show_gesture(True)
        split_view.set_enable_hide_gesture(True)

        navigation = Gtk.ListBox()
        navigation.add_css_class("navigation-sidebar")
        navigation.set_selection_mode(Gtk.SelectionMode.SINGLE)
        navigation.set_activate_on_single_click(True)
        navigation.set_show_separators(False)
        navigation.set_margin_top(12)
        navigation.set_margin_start(12)
        navigation.set_margin_end(12)
        navigation.set_margin_bottom(12)
        navigation.set_vexpand(True)

        workspace_row = self._make_navigation_row(
            "Çalışma Alanı",
            "keyboard-symbolic",
            "workspace",
        )
        statistics_row = self._make_navigation_row(
            "İstatistikler",
            "view-statistics-symbolic",
            "statistics",
        )
        settings_row = self._make_navigation_row(
            "Ayarlar",
            "emblem-system-symbolic",
            "settings",
        )
        navigation.append(workspace_row)
        navigation.append(statistics_row)
        navigation.append(settings_row)
        navigation.select_row(workspace_row)

        # Detach the existing root from ToolbarView before giving it to
        # Gtk.Stack. A widget may have exactly one parent in GTK4.
        toolbar.set_content(None)

        content_stack = Gtk.Stack()
        content_stack.set_hexpand(True)
        content_stack.set_vexpand(True)
        content_stack.add_named(root, "workspace")

        statistics_page = StatisticsPanel()
        statistics_page.set_hexpand(True)
        statistics_page.set_vexpand(True)
        content_stack.add_named(statistics_page, "statistics")

        settings_page = SettingsPanel(self)
        settings_page.set_hexpand(True)
        settings_page.set_vexpand(True)
        content_stack.add_named(settings_page, "settings")
        content_stack.set_visible_child_name("workspace")

        def on_navigation_activated(_list_box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
            page_name = row.get_name()
            if page_name not in {"workspace", "statistics", "settings"}:
                return
            content_stack.set_visible_child_name(page_name)
            split_view.set_show_sidebar(False)

        navigation.connect("row-activated", on_navigation_activated)
        workspace_row.set_name("workspace")
        statistics_row.set_name("statistics")
        settings_row.set_name("settings")

        split_view.set_sidebar(navigation)
        split_view.set_content(content_stack)
        toolbar.set_content(split_view)
        self.sidebar_view = split_view
        self.navigation_list = navigation
        self.content_stack = content_stack

        self.settings_button.set_visible(False)

        show_sidebar_button = Gtk.ToggleButton()
        show_sidebar_button.set_icon_name("sidebar-show-symbolic")
        show_sidebar_button.set_tooltip_text("Yan paneli aç/kapat")
        show_sidebar_button.connect(
            "toggled",
            lambda button: split_view.set_show_sidebar(button.get_active()),
        )
        split_view.connect(
            "notify::show-sidebar",
            lambda view, _param: show_sidebar_button.set_active(view.get_show_sidebar()),
        )
        self.header.pack_start(show_sidebar_button)
        self.sidebar_toggle_button = show_sidebar_button

    @staticmethod
    def _make_navigation_row(title: str, icon_name: str, page_name: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.set_name(page_name)
        row.set_activatable(True)
        row.set_selectable(True)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(18)
        box.append(icon)

        label = Gtk.Label(label=title)
        label.set_xalign(0)
        label.set_hexpand(True)
        box.append(label)
        row.set_child(box)
        return row

    def _load_sources(self) -> None:
        sources = self.db.sources()
        self.source_ids = [i for i, _ in sources]
        self.source_dropdown.set_model(Gtk.StringList.new([n for _, n in sources]))
        if sources:
            self.source_dropdown.set_selected(0)

    def _on_source_changed(self, _dropdown: SourceSearchDropdown, _param) -> None:
        index = self.source_dropdown.get_selected()
        if 0 <= index < len(self.source_ids):
            self._load_lessons(self.source_ids[index])


keycan_window.KeycanWindow = ConfiguredKeycanWindow
keycan_app.KeycanWindow = ConfiguredKeycanWindow


if __name__ == "__main__":
    raise SystemExit(main())
