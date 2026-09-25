"""Stage 7 progression rules for Keycan.

The progression model is deterministic and local. XP is earned from completed
practice sessions, while levels, badges and streaks are derived from history.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime

def session_xp(*, duration_seconds: float, typed_word_count: int, words_per_minute: float, accuracy_percent: float) -> int:
    if typed_word_count <= 0:
        return 0
    return 10 + min(20, int(max(0.0, words_per_minute) / 5)) + min(20, int(max(0.0, accuracy_percent) / 5)) + min(10, int(max(0.0, duration_seconds) / 60))

def xp_for_level(level: int) -> int:
    level = max(1, int(level))
    return 50 * (level - 1) * level

def level_for_xp(xp: int) -> int:
    xp = max(0, int(xp))
    level = 1
    while xp >= xp_for_level(level + 1):
        level += 1
    return level

def level_progress(xp: int) -> tuple[int, int, int]:
    level = level_for_xp(xp)
    current = xp_for_level(level)
    next_level = xp_for_level(level + 1)
    return level, xp - current, next_level - current

@dataclass(frozen=True)
class Badge:
    key: str
    title: str
    description: str

BADGES = (
    Badge("first_session", "İlk Adım", "İlk yazma çalışmanı tamamla."),
    Badge("ten_sessions", "Düzenli Pratik", "10 yazma çalışmasını tamamla."),
    Badge("fifty_sessions", "Alışkanlık", "50 yazma çalışmasını tamamla."),
    Badge("hundred_sessions", "Usta Çırak", "100 yazma çalışmasını tamamla."),
    Badge("speed_40", "Hızlandı", "40 WPM hızına ulaş."),
    Badge("speed_60", "Hızlı Yazıcı", "60 WPM hızına ulaş."),
    Badge("accuracy_95", "Keskinlik", "%95 doğruluğa ulaş."),
    Badge("accuracy_98", "Nokta Atışı", "%98 doğruluğa ulaş."),
    Badge("long_session", "Dayanıklılık", "10 dakikalık bir çalışma tamamla."),
    Badge("streak_7", "7 Günlük Seri", "7 gün üst üste pratik yap."),
    Badge("streak_30", "30 Günlük Seri", "30 gün üst üste pratik yap."),
    Badge("xp_1000", "Binlik", "1.000 XP kazan."),
)

def badge_keys(*, sessions: int, max_wpm: float, max_accuracy: float, max_duration_seconds: float, best_streak: int, xp: int) -> set[str]:
    checks = {
        "first_session": sessions >= 1, "ten_sessions": sessions >= 10,
        "fifty_sessions": sessions >= 50, "hundred_sessions": sessions >= 100,
        "speed_40": max_wpm >= 40, "speed_60": max_wpm >= 60,
        "accuracy_95": max_accuracy >= 95, "accuracy_98": max_accuracy >= 98,
        "long_session": max_duration_seconds >= 600, "streak_7": best_streak >= 7,
        "streak_30": best_streak >= 30, "xp_1000": xp >= 1000,
    }
    return {key for key, unlocked in checks.items() if unlocked}

def _local_days(timestamps: list[str]) -> list[date]:
    days = set()
    for value in timestamps:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        days.add(parsed.date())
    return sorted(days)

def streaks(timestamps: list[str], today: date | None = None) -> tuple[int, int]:
    days = _local_days(timestamps)
    if not days:
        return 0, 0
    best = current = 1
    for previous, current_day in zip(days, days[1:]):
        if (current_day - previous).days == 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    reference = today or date.today()
    if days[-1] == reference:
        current_streak = 1
        index = len(days) - 1
        while index > 0 and (days[index] - days[index - 1]).days == 1:
            current_streak += 1
            index -= 1
    else:
        current_streak = 0
    return current_streak, best
