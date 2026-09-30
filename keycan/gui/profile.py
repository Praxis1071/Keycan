"""Stage 8 local profile dashboard for Keycan."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import gi

gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from keycan.services.progression import BADGES, badge_keys, level_progress, next_goal
from keycan.services.translations import translate


class ProfilePanel(Gtk.Box):
    def __init__(self, database) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.db = database
        self.language = "tr"
        self._profile_path = self._config_dir() / "profile.json"
        self._photo_path: Path | None = None
        self._profile_name = ""
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_halign(Gtk.Align.FILL)
        self._build()
        self._load_profile()
        self.refresh()

    @staticmethod
    def _config_dir() -> Path:
        return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "keycan"

    @staticmethod
    def _data_dir() -> Path:
        return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "keycan"

    def _build(self) -> None:
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        header.set_halign(Gtk.Align.FILL)

        self.avatar = Gtk.Picture()
        self.avatar.set_size_request(88, 88)
        self.avatar.set_can_shrink(False)
        self.avatar.set_content_fit(Gtk.ContentFit.COVER)
        self.avatar.add_css_class("card")
        header.append(self.avatar)

        identity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        identity.set_valign(Gtk.Align.CENTER)
        identity.set_hexpand(True)

        self.title = Gtk.Label(label="Profil")
        self.title.set_xalign(0)
        self.title.add_css_class("title-1")
        identity.append(self.title)

        self.subtitle = Gtk.Label(label="Yerel ilerlemen ve başarıların")
        self.subtitle.set_xalign(0)
        self.subtitle.add_css_class("dim-label")
        self.subtitle.set_wrap(True)
        identity.append(self.subtitle)

        self.photo_button = Gtk.Button(label="Profil fotoğrafı seç")
        self.photo_button.set_halign(Gtk.Align.START)
        self.photo_button.connect("clicked", self._choose_photo)
        identity.append(self.photo_button)
        header.append(identity)
        self.append(header)

        identity_group = Adw.PreferencesGroup()
        identity_group.set_title("Profil bilgileri")
        identity_group.set_description("Adını ve yerel profilini düzenle.")
        self.append(identity_group)

        self.name_row = Adw.EntryRow()
        self.name_row.set_title("Ad")
        self.name_row.set_text("")
        self.name_row.connect("apply", self._save_name)
        identity_group.add(self.name_row)

        level_group = Adw.PreferencesGroup()
        level_group.set_title("Seviye ilerlemesi")
        level_group.set_description("XP kazandıkça seviye atla ve bir sonraki seviyeye ilerle.")
        self.append(level_group)

        level_row = Adw.ActionRow()
        self.level_label = Gtk.Label()
        self.level_label.add_css_class("title-2")
        self.level_label.set_xalign(0)
        level_row.add_prefix(self.level_label)

        level_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        level_content.set_hexpand(True)
        self.progress = Gtk.ProgressBar()
        self.progress.set_hexpand(True)
        self.xp_label = Gtk.Label()
        self.xp_label.set_xalign(1)
        self.xp_label.add_css_class("dim-label")
        level_content.append(self.progress)
        level_content.append(self.xp_label)
        level_row.add_suffix(level_content)
        level_group.add(level_row)

        self.next_level = Gtk.Label()
        self.next_level.set_xalign(0)
        self.next_level.add_css_class("dim-label")
        self.next_level.set_wrap(True)
        level_group.add(self.next_level)

        goal_group = Adw.PreferencesGroup()
        goal_group.set_title("Sonraki hedef")
        goal_group.set_description("Mevcut ilerlemene göre ulaşabileceğin bir sonraki kilometre taşı.")
        self.append(goal_group)
        self.goal_row = Adw.ActionRow()
        self.goal_row.set_activatable(False)
        self.goal_icon = Gtk.Image.new_from_icon_name("target-symbolic")
        self.goal_icon.set_pixel_size(20)
        self.goal_row.add_prefix(self.goal_icon)
        self.goal_label = Gtk.Label()
        self.goal_label.set_xalign(0)
        self.goal_label.set_wrap(True)
        self.goal_label.set_hexpand(True)
        self.goal_row.add_suffix(self.goal_label)
        goal_group.add(self.goal_row)

        stats = Adw.PreferencesGroup()
        stats.set_title("İlerleme özeti")
        stats.set_description("Çalışma alışkanlıkların ve genel performansın.")
        self.append(stats)

        self.session_row = self._stat_row(stats, "Çalışmalar")
        self.xp_total_row = self._stat_row(stats, "Toplam XP")
        self.current_streak_row = self._stat_row(stats, "Mevcut seri")
        self.best_streak_row = self._stat_row(stats, "En uzun seri")
        self.wpm_row = self._stat_row(stats, "En yüksek hız")
        self.average_wpm_row = self._stat_row(stats, "Ortalama hız")
        self.accuracy_row = self._stat_row(stats, "En yüksek doğruluk")
        self.average_accuracy_row = self._stat_row(stats, "Ortalama doğruluk")
        self.duration_row = self._stat_row(stats, "En uzun çalışma")
        self.total_duration_row = self._stat_row(stats, "Toplam çalışma süresi")
        self.words_row = self._stat_row(stats, "Toplam kelime")
        self.characters_row = self._stat_row(stats, "Toplam karakter")
        self.lessons_row = self._stat_row(stats, "Tamamlanan dersler")

        history = Adw.PreferencesGroup()
        history.set_title("Son çalışmalar")
        history.set_description("En son tamamladığın çalışmaların kısa özeti.")
        self.append(history)
        self.history_group = history

        badges = Adw.PreferencesGroup()
        badges.set_title("Rozetler")
        badges.set_description("Tamamladığın kilometre taşları.")
        self.append(badges)

        self.badges_box = Gtk.FlowBox()
        self.badges_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.badges_box.set_row_spacing(6)
        self.badges_box.set_column_spacing(6)
        self.badges_box.set_min_children_per_line(1)
        self.badges_box.set_max_children_per_line(3)
        self.badges_box.set_hexpand(True)
        badges.add(self.badges_box)

        self.empty = Gtk.Label(label="")
        self.empty.set_xalign(0)
        self.empty.set_wrap(True)
        self.empty.add_css_class("dim-label")
        badges.add(self.empty)

    @staticmethod
    def _stat_row(group, title):
        row = Adw.ActionRow()
        row.set_title(title)
        value = Gtk.Label()
        value.add_css_class("monospace")
        row.add_suffix(value)
        group.add(row)
        row._value_label = value
        return row

    def set_language(self, language: str) -> None:
        self.language = language
        from keycan.services.i18n import apply_to_widget_tree
        apply_to_widget_tree(self, language)
        self.refresh()

    def _load_profile(self) -> None:
        try:
            data = json.loads(self._profile_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            return
        name = data.get("name")
        if isinstance(name, str):
            self._profile_name = name.strip()[:80]
            self.name_row.set_text(self._profile_name)
        photo = data.get("photo")
        if isinstance(photo, str) and photo:
            path = Path(photo).expanduser()
            if path.is_file():
                self._photo_path = path
                self._set_photo(path)

    def _save_profile(self) -> None:
        self._profile_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"name": self._profile_name, "photo": str(self._photo_path) if self._photo_path else ""},
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        self._profile_path.write_text(payload, encoding="utf-8")

    def _save_name(self, row) -> None:
        self._profile_name = row.get_text().strip()[:80]
        row.set_text(self._profile_name)
        self._save_profile()
        self.refresh()

    def _choose_photo(self, _button) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title(translate("Profil fotoğrafı seç", self.language))
        dialog.set_modal(True)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        image_filter = Gtk.FileFilter()
        image_filter.set_name(translate("Görsel dosyaları", self.language))
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            image_filter.add_pattern(pattern)
        filters.append(image_filter)
        dialog.set_filters(filters)
        root = self.get_root()
        if not isinstance(root, Gtk.Window):
            return
        dialog.open(root, None, self._photo_selected)

    def _photo_selected(self, dialog, result) -> None:
        try:
            source = dialog.open_finish(result)
        except GLib.Error:
            return
        if source is None:
            return
        try:
            self._data_dir().mkdir(parents=True, exist_ok=True)
            basename = source.get_basename() or "profile.png"
            suffix = basename.rsplit(".", 1)[-1].lower()
            if suffix not in {"png", "jpg", "jpeg", "webp"}:
                suffix = "png"
            destination = self._data_dir() / f"profile-photo.{suffix}"
            for old in self._data_dir().glob("profile-photo.*"):
                if old != destination:
                    old.unlink(missing_ok=True)
            source_path = Path(source.get_path() or "")
            if not source_path.is_file():
                return
            shutil.copy2(source_path, destination)
        except (OSError, TypeError):
            return
        self._photo_path = destination
        self._set_photo(destination)
        self._save_profile()

    def _set_photo(self, path: Path) -> None:
        try:
            texture = Gdk.Texture.new_from_filename(str(path))
        except GLib.Error:
            return
        self.avatar.set_paintable(texture)

    def refresh(self) -> None:
        data = self.db.progression_summary()
        xp = int(data["xp"])
        level, into, span = level_progress(xp)
        remaining = max(0, span - into)

        self.level_label.set_text(translate(f"Seviye {level}", self.language))
        self.xp_label.set_text(translate(f"{into} / {span} XP", self.language))
        self.progress.set_fraction(into / span if span else 1.0)
        self.next_level.set_text(
            translate(f"Sonraki seviye için {remaining} XP", self.language)
        )

        sessions = int(data["sessions"])
        current_streak = int(data["current_streak"])
        best_streak = int(data["best_streak"])
        max_wpm = float(data["max_wpm"])
        max_accuracy = float(data["max_accuracy"])
        max_duration = float(data["max_duration_seconds"])

        self.session_row._value_label.set_text(str(sessions))
        self.xp_total_row._value_label.set_text(str(xp))
        self.current_streak_row._value_label.set_text(translate(f"{current_streak} gün", self.language))
        self.best_streak_row._value_label.set_text(translate(f"{best_streak} gün", self.language))
        self.wpm_row._value_label.set_text(f"{max_wpm:.1f} WPM")
        self.average_wpm_row._value_label.set_text(f"{float(data['average_wpm']):.1f} WPM")
        self.accuracy_row._value_label.set_text(f"{max_accuracy:.1f}%")
        self.average_accuracy_row._value_label.set_text(f"{float(data['average_accuracy']):.1f}%")
        self.duration_row._value_label.set_text(translate(self._format_duration(max_duration), self.language))
        self.total_duration_row._value_label.set_text(translate(self._format_duration(float(data["total_duration_seconds"])), self.language))
        self.words_row._value_label.set_text(f"{int(data['total_words']):,}".replace(",", " "))
        self.characters_row._value_label.set_text(f"{int(data['total_characters']):,}".replace(",", " "))
        self.lessons_row._value_label.set_text(str(int(data["completed_lessons"])))

        self._refresh_history(data.get("recent_sessions", []))

        goal = next_goal(
            sessions=sessions,
            max_wpm=max_wpm,
            max_accuracy=max_accuracy,
            max_duration_seconds=max_duration,
            best_streak=best_streak,
            xp=xp,
        )
        if goal is None:
            self.goal_label.set_text(translate("Tüm mevcut rozet hedefleri tamamlandı.", self.language))
        else:
            badge, current, target = goal
            self.goal_label.set_text(
                f"{translate(badge.title, self.language)}: {self._goal_progress_text(badge.key, current, target)}"
            )

        unlocked = badge_keys(
            sessions=sessions, max_wpm=max_wpm, max_accuracy=max_accuracy,
            max_duration_seconds=max_duration, best_streak=best_streak, xp=xp,
        )
        self._clear_badges()
        for badge in BADGES:
            self.badges_box.insert(self._badge_card(badge, badge.key in unlocked), -1)
        self.empty.set_text(
            translate(f"{len(unlocked)} / {len(BADGES)} rozet açıldı.", self.language)
        )
        self.title.set_text(self._profile_name or translate("Profil", self.language))

    def _refresh_history(self, sessions) -> None:
        child = self.history_group.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.history_group.remove(child)
            child = next_child
        if not sessions:
            row = Adw.ActionRow()
            row.set_title(translate("Henüz çalışma yok", self.language))
            self.history_group.add(row)
            return
        for item in sessions:
            row = Adw.ActionRow()
            row.set_title(f"{float(item['wpm']):.1f} WPM · {float(item['accuracy']):.1f}%")
            row.set_subtitle(
                f"{self._format_duration(float(item['duration_seconds']))} · "
                f"{item['completed_at']}"
            )
            self.history_group.add(row)

    def _goal_progress_text(self, key: str, current: float, target: float) -> str:
        if key in {"speed_40", "speed_60"}:
            return f"{current:.1f} / {target:.0f} WPM"
        if key in {"accuracy_95", "accuracy_98"}:
            return f"{current:.1f} / {target:.0f}%"
        if key == "long_session":
            return f"{int(current)} / {int(target)} s"
        return f"{int(current)} / {int(target)}"

    def _clear_badges(self) -> None:
        child = self.badges_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.badges_box.remove(child)
            child = next_child

    def _badge_card(self, badge, unlocked: bool) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(10)
        card.set_margin_end(10)
        card.set_size_request(170, 82)
        card.set_sensitive(unlocked)
        icon = Gtk.Image.new_from_icon_name("starred-symbolic" if unlocked else "changes-prevent-symbolic")
        icon.set_pixel_size(18)
        icon.set_halign(Gtk.Align.START)
        card.append(icon)
        title = Gtk.Label(label=translate(badge.title, self.language))
        title.set_xalign(0)
        title.set_wrap(True)
        title.add_css_class("heading")
        card.append(title)
        description = Gtk.Label(label=translate(badge.description, self.language))
        description.set_xalign(0)
        description.set_wrap(True)
        description.add_css_class("dim-label")
        card.append(description)
        return card

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total_minutes = int(max(0.0, seconds) // 60)
        if total_minutes < 1:
            return "1 dakikadan kısa"
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            return f"{hours} sa {minutes} dk"
        return f"{minutes} dk"
