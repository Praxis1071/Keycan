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
        split_view.set_min_sidebar_width(280)
        split_view.set_max_sidebar_width(360)
        split_view.set_sidebar_width_fraction(0.30)
        split_view.set_show_sidebar(False)
        split_view.set_enable_show_gesture(True)
        split_view.set_enable_hide_gesture(True)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar.add_css_class("keycan-sidebar")
        sidebar_provider = Gtk.CssProvider()
        sidebar_provider.load_from_data(
            ".keycan-sidebar { background: #202124; color: #eeeeee; }"
            ".keycan-sidebar label { color: #eeeeee; }",
            -1,
        )
        sidebar.get_style_context().add_provider(
            sidebar_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sidebar_header.set_margin_top(12)
        sidebar_header.set_margin_bottom(8)
        sidebar_header.set_margin_start(12)
        sidebar_header.set_margin_end(12)
        title = Gtk.Label(label="Keycan")
        title.set_xalign(0)
        title.set_hexpand(True)
        title.add_css_class("title-3")
        sidebar_header.append(title)

        close_button = Gtk.Button()
        close_button.set_icon_name("sidebar-hide-symbolic")
        close_button.set_tooltip_text("Paneli kapat")
        close_button.add_css_class("flat")
        close_button.connect("clicked", lambda _button: split_view.set_show_sidebar(False))
        sidebar_header.append(close_button)
        sidebar.append(sidebar_header)
        sidebar.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav.set_margin_top(10)
        nav.set_margin_start(12)
        nav.set_margin_end(12)
        settings_button = Gtk.ToggleButton(label="⚙  Ayarlar")
        settings_button.set_active(True)
        settings_button.set_hexpand(True)
        nav.append(settings_button)
        sidebar.append(nav)

        settings_panel = SettingsPanel(self)
        settings_panel.set_vexpand(True)
        sidebar.append(settings_panel)

        split_view.set_sidebar(sidebar)
        split_view.set_content(root)
        toolbar.set_content(split_view)
        self.sidebar_view = split_view

        self.settings_button.set_visible(False)
        controls = root.get_first_child()
        if isinstance(controls, Gtk.Box):
            panel_button = Gtk.Button()
            panel_button.set_icon_name("sidebar-show-symbolic")
            panel_button.set_tooltip_text("Yan panel")
            panel_button.add_css_class("flat")
            panel_button.connect(
                "clicked",
                lambda _button: split_view.set_show_sidebar(not split_view.get_show_sidebar()),
            )
            controls.prepend(panel_button)

        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 900sp"))
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
