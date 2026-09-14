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

        self._install_sidebar()

    def _install_sidebar(self) -> None:
        toolbar = self.get_content()
        if not isinstance(toolbar, Adw.ToolbarView):
            return
        root = toolbar.get_content()
        if not isinstance(root, Gtk.Box):
            return

        split_view = Adw.OverlaySplitView()
        split_view.set_sidebar_position(Gtk.PackType.START)
        split_view.set_min_sidebar_width(260)
        split_view.set_max_sidebar_width(340)
        split_view.set_sidebar_width_fraction(0.25)
        split_view.set_show_sidebar(False)
        split_view.set_enable_show_gesture(True)
        split_view.set_enable_hide_gesture(True)

        # Settings lives in a utility pane below the shared window header bar.
        # The structure is ready for future Dashboard/Profile pages without
        # changing the main typing workspace.
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_toolbar.set_top_bar_style(Adw.ToolbarStyle.FLAT)

        sidebar_header = Adw.HeaderBar()
        sidebar_title = Gtk.Label(label="Keycan")
        sidebar_title.add_css_class("title-3")
        sidebar_header.set_title_widget(sidebar_title)
        sidebar_toolbar.add_top_bar(sidebar_header)

        sidebar_body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sidebar_body.set_margin_top(12)
        sidebar_body.set_margin_start(12)
        sidebar_body.set_margin_end(12)
        sidebar_body.set_margin_bottom(12)

        navigation = Gtk.ListBox()
        navigation.add_css_class("navigation-sidebar")
        navigation.set_selection_mode(Gtk.SelectionMode.SINGLE)
        navigation.set_activate_on_single_click(True)
        navigation.set_show_separators(False)

        settings_row = Gtk.ListBoxRow()
        settings_row.set_activatable(True)
        settings_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        settings_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        settings_icon.set_pixel_size(18)
        settings_row_box.append(settings_icon)
        settings_label = Gtk.Label(label="Ayarlar")
        settings_label.set_xalign(0)
        settings_row_box.append(settings_label)
        settings_row.set_child(settings_row_box)
        navigation.append(settings_row)
        navigation.select_row(settings_row)
        sidebar_body.append(navigation)

        settings_scroll = Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_scroll.set_vexpand(True)
        settings_panel = SettingsPanel(self)
        settings_panel.set_margin_top(0)
        settings_panel.set_margin_bottom(0)
        settings_panel.set_margin_start(8)
        settings_panel.set_margin_end(8)
        settings_scroll.set_child(settings_panel)
        sidebar_body.append(settings_scroll)

        sidebar_toolbar.set_content(sidebar_body)
        split_view.set_sidebar(sidebar_toolbar)

        # The existing root is already owned by the ToolbarView. Detach it
        # before assigning it to the split view to preserve the main content.
        toolbar.set_content(None)
        split_view.set_content(root)
        toolbar.set_content(split_view)
        self.sidebar_view = split_view

        self.settings_button.set_visible(False)

        # The sidebar toggle belongs in the shared header bar, not in the
        # lesson controls row. This keeps the typing workspace unchanged.
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

        breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 900sp")
        )
        breakpoint.add_setter(split_view, "collapsed", True)
        self.add_breakpoint(breakpoint)

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
