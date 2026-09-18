#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

import keycan.app as keycan_app
import keycan.data.database_runtime  # noqa: F401 — installs custom content and backup behavior.
import keycan.window as keycan_window
from keycan.app import main
from keycan.gui.search import SourceSearchDropdown
import keycan.gui.statistics_runtime  # noqa: F401 — prevents stale KPI animations.
from keycan.gui.settings2 import SettingsPanel
from keycan.gui.statistics_clean import StatisticsPanel


class ConfiguredKeycanWindow(keycan_window.KeycanWindow):
    def __init__(self, app: Adw.Application, database_path):
        super().__init__(app, database_path)
        self.maximize(); self.text_size=22; self.size_spin.set_value(22); self.workspace.set_text_size(self.text_size)
    def _build_ui(self):
        super()._build_ui(); old=self.source_dropdown; parent=old.get_parent(); previous=old.get_prev_sibling() if parent is not None else None; self.source_dropdown=SourceSearchDropdown(); self.source_dropdown.on_selected_changed=self._on_source_changed; self.source_dropdown.set_hexpand(True); self.source_dropdown.set_halign(Gtk.Align.FILL)
        if parent is not None:
            old.unparent(); self.source_dropdown.insert_after(parent,previous) if previous is not None else parent.append(self.source_dropdown)
        self._install_sidebar_navigation()
        compact_height = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-height: 650sp")
        )
        compact_height.add_setter(self.workspace.editors, "position", 280)
        self.add_breakpoint(compact_height)
        short_height = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-height: 520sp")
        )
        short_height.add_setter(self.workspace.editors, "position", 210)
        short_height.add_setter(self.workspace.bottom, "height-request", 30)
        self.add_breakpoint(short_height)
    def _install_sidebar_navigation(self):
        toolbar=self.get_content()
        if not isinstance(toolbar,Adw.ToolbarView):return
        root=toolbar.get_content()
        if not isinstance(root,Gtk.Box):return
        split=Adw.OverlaySplitView();split.set_collapsed(True);split.set_sidebar_position(Gtk.PackType.START);split.set_min_sidebar_width(260);split.set_max_sidebar_width(340);split.set_sidebar_width_fraction(.25);split.set_show_sidebar(False);split.set_enable_show_gesture(True);split.set_enable_hide_gesture(True)
        nav=Gtk.ListBox();nav.add_css_class("navigation-sidebar");nav.set_selection_mode(Gtk.SelectionMode.SINGLE);nav.set_activate_on_single_click(True);nav.set_show_separators(False);nav.set_margin_top(12);nav.set_margin_start(12);nav.set_margin_end(12);nav.set_margin_bottom(12);nav.set_vexpand(True)
        workspace_row=self._make_navigation_row("Çalışma Alanı","input-keyboard-symbolic","workspace");statistics_row=self._make_navigation_row("İstatistikler","utilities-system-monitor-symbolic","statistics");settings_row=self._make_navigation_row("Ayarlar","emblem-system-symbolic","settings")
        nav.append(workspace_row);nav.append(statistics_row);nav.append(settings_row);nav.select_row(workspace_row);toolbar.set_content(None)
        stack=Gtk.Stack();stack.set_hexpand(True);stack.set_vexpand(True);stack.add_named(root,"workspace")
        stats=StatisticsPanel(self.db);stats.set_hexpand(True);stats.set_vexpand(True);stack.add_named(stats,"statistics")
        settings=SettingsPanel(self,on_content_changed=self._load_sources,on_statistics_changed=stats.refresh)
        settings.set_hexpand(True)
        settings.set_vexpand(True)
        settings_scroll=Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        settings_scroll.set_hexpand(True)
        settings_scroll.set_vexpand(True)
        settings_scroll.set_child(settings)
        stack.add_named(settings_scroll,"settings")
        stack.set_visible_child_name("workspace")
        def activated(_list,row):
            name=row.get_name()
            if name not in {"workspace","statistics","settings"}:return
            stack.set_visible_child_name(name)
            if name=="statistics":stats.refresh()
            split.set_show_sidebar(False)
        nav.connect("row-activated",activated);workspace_row.set_name("workspace");statistics_row.set_name("statistics");settings_row.set_name("settings");split.set_sidebar(nav);split.set_content(stack);toolbar.set_content(split)
        self.sidebar_view=split;self.navigation_list=nav;self.content_stack=stack;self.statistics_page=stats
        toggle=Gtk.ToggleButton();toggle.set_icon_name("sidebar-show-symbolic");toggle.set_tooltip_text("Yan paneli aç/kapat");toggle.connect("toggled",lambda b:split.set_show_sidebar(b.get_active()));split.connect("notify::show-sidebar",lambda v,_p:toggle.set_active(v.get_show_sidebar()));self.header.pack_start(toggle);self.sidebar_toggle_button=toggle
    @staticmethod
    def _make_navigation_row(title,icon_name,page_name):
        row=Gtk.ListBoxRow();row.set_name(page_name);row.set_activatable(True);row.set_selectable(True);box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10);icon=Gtk.Image.new_from_icon_name(icon_name);icon.set_pixel_size(18);box.append(icon);label=Gtk.Label(label=title);label.set_xalign(0);label.set_hexpand(True);box.append(label);row.set_child(box);return row
    def _load_sources(self):
        sources=self.db.sources();self.source_ids=[i for i,_ in sources];self.source_dropdown.set_model(Gtk.StringList.new([n for _,n in sources]))
        if sources:self.source_dropdown.set_selected(0)
        else:
            self.lesson_ids=[]
            self.lesson_dropdown.set_model(Gtk.StringList.new([]))
            self.current_lesson_id=None; self.current_text=""; self._restart()
    def _on_source_changed(self,_dropdown,_param):
        index=self.source_dropdown.get_selected()
        if 0<=index<len(self.source_ids):self._load_lessons(self.source_ids[index])


keycan_window.KeycanWindow=ConfiguredKeycanWindow
keycan_app.KeycanWindow=ConfiguredKeycanWindow

if __name__=="__main__":raise SystemExit(main())
