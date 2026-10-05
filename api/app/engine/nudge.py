"""Scroll behavior tracker and nudge detection engine."""

from dataclasses import dataclass
from typing import Dict, Optional
from ..config import CONFIG


@dataclass
class ScrollMetrics:
    active_scroll_seconds: float
    reversals_count: int
    rows_scrolled: int
    months_scrolled: int
    last_found_seconds_ago: Optional[float] = None
    dismiss_count_recent: int = 0


def evaluate_nudge_trigger(metrics: ScrollMetrics) -> bool:
    """Evaluate whether user is struggling to find a photo and should receive a gentle search nudge."""
    cfg = CONFIG.nudge

    # Cooldown check: quiet period after found photo
    if metrics.last_found_seconds_ago is not None and metrics.last_found_seconds_ago < cfg.quiet_after_found_s:
        return False

    # Dismiss suppression limit
    if metrics.dismiss_count_recent >= cfg.dismiss_limit:
        return False

    # Primary trigger conditions (any of these indicate search struggle)
    time_triggered = metrics.active_scroll_seconds >= cfg.seconds
    reversals_triggered = metrics.reversals_count >= cfg.reversals
    distance_triggered = (
        metrics.rows_scrolled >= cfg.rows_scrolled
        or metrics.months_scrolled >= cfg.months_scrolled
    )

    return time_triggered or reversals_triggered or distance_triggered
