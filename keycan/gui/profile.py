"""Stage 7 profile page for Keycan."""
from __future__ import annotations
import gi
gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk
from keycan.services.progression import BADGES, badge_keys, level_progress
from keycan.services.translations import translate

class ProfilePanel(Gtk.Box):
    def __init__(self, database) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.db = database
        self.set_margin_top(24); self.set_margin_bottom(24)
        self.set_margin_start(20); self.set_margin_end(20)
        self._build(); self.refresh()

    def _build(self) -> None:
        title = Gtk.Label(label="Profil"); title.set_xalign(0); title.add_css_class("title-1"); self.append(title)
        self.summary = Gtk.Label(); self.summary.set_xalign(0); self.summary.set_wrap(True); self.summary.add_css_class("dim-label"); self.append(self.summary)
        progress_group = Adw.PreferencesGroup(); progress_group.set_title("Seviye ilerlemesi"); self.append(progress_group)
        progress_row = Adw.ActionRow(); self.level_label = Gtk.Label(); self.level_label.add_css_class("title-2"); progress_row.add_prefix(self.level_label)
        self.xp_label = Gtk.Label(); self.xp_label.add_css_class("monospace"); progress_row.add_suffix(self.xp_label)
        self.progress = Gtk.ProgressBar(); self.progress.set_hexpand(True); progress_row.add_suffix(self.progress); progress_group.add(progress_row)
        stats = Adw.PreferencesGroup(); stats.set_title("İlerleme özeti"); self.append(stats)
        self.session_row = self._stat_row(stats, "Çalışmalar"); self.streak_row = self._stat_row(stats, "Mevcut seri")
        self.best_streak_row = self._stat_row(stats, "En uzun seri"); self.xp_total_row = self._stat_row(stats, "Toplam XP")
        badge_group = Adw.PreferencesGroup(); badge_group.set_title("Rozetler"); badge_group.set_description("Tamamladığın kilometre taşları."); self.append(badge_group)
        self.badges_box = Gtk.FlowBox(); self.badges_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.badges_box.set_row_spacing(8); self.badges_box.set_column_spacing(8); self.badges_box.set_max_children_per_line(3); self.badges_box.set_min_children_per_line(1)
        badge_group.add(self.badges_box)
        self.empty = Gtk.Label(label=translate("Henüz rozet kazanılmadı.", self.language)); self.empty.set_xalign(0); self.empty.add_css_class("dim-label"); badge_group.add(self.empty)

    @staticmethod
    def _stat_row(group, title):
        row = Adw.ActionRow(); row.set_title(title); row.add_css_class("property")
        value = Gtk.Label(); value.add_css_class("monospace"); row.add_suffix(value); group.add(row); row._value_label = value
        return row

    def refresh(self) -> None:
        data = self.db.progression_summary()
        xp = int(data["xp"]); level, into, span = level_progress(xp)
        self.level_label.set_text(translate(f"Seviye {level}", self.language)); self.xp_label.set_text(f"{into} / {span} XP"); self.progress.set_fraction(into / span if span else 1.0)
        sessions = int(data["sessions"]); current_streak = int(data["current_streak"]); best_streak = int(data["best_streak"])
        self.summary.set_text(translate(f"{sessions} çalışma · {xp} XP · {current_streak} gün mevcut seri", self.language))
        self.session_row._value_label.set_text(str(sessions)); self.streak_row._value_label.set_text(translate(f"{current_streak} gün", self.language))
        self.best_streak_row._value_label.set_text(translate(f"{best_streak} gün", self.language)); self.xp_total_row._value_label.set_text(str(xp))
        unlocked = badge_keys(sessions=sessions, max_wpm=float(data["max_wpm"]), max_accuracy=float(data["max_accuracy"]), max_duration_seconds=float(data["max_duration_seconds"]), best_streak=best_streak, xp=xp)
        child = self.badges_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling(); self.badges_box.remove(child); child = next_child
        for badge in BADGES:
            if badge.key not in unlocked: continue
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.set_margin_top(10); card.set_margin_bottom(10); card.set_margin_start(12); card.set_margin_end(12); card.set_size_request(170, 74)
            icon = Gtk.Image.new_from_icon_name("starred-symbolic"); icon.set_pixel_size(20); icon.set_halign(Gtk.Align.START); card.append(icon)
            title = Gtk.Label(label=translate(badge.title, self.language)); title.set_xalign(0); title.add_css_class("heading"); card.append(title)
            description = Gtk.Label(label=translate(badge.description, self.language)); description.set_xalign(0); description.set_wrap(True); description.add_css_class("dim-label"); card.append(description)
            self.badges_box.insert(card, -1)
        self.empty.set_text(translate("Henüz rozet kazanılmadı.", self.language))
        self.empty.set_visible(not unlocked)
