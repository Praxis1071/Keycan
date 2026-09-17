"""Runtime hardening for statistics animations.

A refreshed dashboard must have only one active animation per metric card.
Otherwise an old GLib timeout can keep writing stale values after statistics
are reset, making the displayed numbers appear to increase by themselves.
"""

from __future__ import annotations

from gi.repository import GLib

from keycan.gui.statistics_clean import MetricCard


_original_set_value = MetricCard.set_value


def _set_value_safe(self: MetricCard, value: float, formatter=None, suffix: str = "") -> None:
    source_id = getattr(self, "_metric_animation_source", 0)
    if source_id:
        try:
            GLib.source_remove(source_id)
        except (TypeError, ValueError):
            pass
        self._metric_animation_source = 0

    target = max(0.0, float(value))
    formatter = formatter or (lambda n: f"{n:.0f}")
    self._target = target

    # A reset is a state change, not an animation. This also guarantees that
    # no stale callback can write a previous value back into the label.
    if target == 0.0:
        self.value.set_text(f"{formatter(0)}{suffix}")
        return

    current = 0.0
    self.value.set_text(f"{formatter(0)}{suffix}")

    def tick() -> bool:
        nonlocal current
        # The source may have been replaced by a newer refresh.
        if getattr(self, "_metric_animation_source", 0) != source_holder[0]:
            return False
        current += max(0.5, (target - current) * 0.18)
        if abs(target - current) < 0.5:
            current = target
        self.value.set_text(f"{formatter(current)}{suffix}")
        if current == target:
            self._metric_animation_source = 0
            return False
        return True

    source_holder = [0]
    source_holder[0] = GLib.timeout_add(16, tick)
    self._metric_animation_source = source_holder[0]


MetricCard.set_value = _set_value_safe
