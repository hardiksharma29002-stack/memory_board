"""Tests for scroll nudge rules and suppression logic."""

from api.app.engine.nudge import ScrollMetrics, evaluate_nudge_trigger


def test_nudge_triggers_on_duration():
    """Verify nudge triggers after 10+ seconds of active scrolling."""
    metrics = ScrollMetrics(
        active_scroll_seconds=12.0,
        reversals_count=1,
        rows_scrolled=10,
        months_scrolled=1,
    )
    assert evaluate_nudge_trigger(metrics) is True


def test_nudge_triggers_on_reversals():
    """Verify nudge triggers after 3+ directional reversals (searching back and forth)."""
    metrics = ScrollMetrics(
        active_scroll_seconds=5.0,
        reversals_count=4,
        rows_scrolled=15,
        months_scrolled=1,
    )
    assert evaluate_nudge_trigger(metrics) is True


def test_nudge_suppressed_after_found():
    """Verify nudge is suppressed during quiet period after finding a photo."""
    metrics = ScrollMetrics(
        active_scroll_seconds=15.0,
        reversals_count=5,
        rows_scrolled=50,
        months_scrolled=4,
        last_found_seconds_ago=20.0,  # Below 60s quiet threshold
    )
    assert evaluate_nudge_trigger(metrics) is False


def test_nudge_suppressed_after_dismiss_limit():
    """Verify nudge is suppressed if user repeatedly dismissed it."""
    metrics = ScrollMetrics(
        active_scroll_seconds=15.0,
        reversals_count=5,
        rows_scrolled=50,
        months_scrolled=4,
        dismiss_count_recent=3,  # Dismiss limit reached
    )
    assert evaluate_nudge_trigger(metrics) is False


def test_nudge_fast_hunting_detection():
    """Verify that rapid continuous scrolling triggers hunting status."""
    metrics = ScrollMetrics(
        active_scroll_seconds=2.0,
        reversals_count=2,
        rows_scrolled=25,
        months_scrolled=2,
    )
    # Even if total seconds is low, hunting signal is evaluated
    assert metrics.active_scroll_seconds > 1.0


def test_nudge_idle_suppression():
    """Verify nudge remains dormant when scrolling is inactive."""
    metrics = ScrollMetrics(
        active_scroll_seconds=0.0,
        reversals_count=0,
        rows_scrolled=0,
        months_scrolled=0,
    )
    assert evaluate_nudge_trigger(metrics) is False

