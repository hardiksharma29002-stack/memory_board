"""Tests for evaluation metrics and simulation logic."""

from eval.metrics import compute_found_in_k, compute_mean_steps, compute_ece, compute_none_of_these_rate
from eval.calibrate import train_calibrator, calibrate_score
from eval.baselines import run_baseline_b1_scroll, run_baseline_b2_text_query


def test_metrics_computations():
    """Verify metrics calculate accurately."""
    sessions = [
        {"outcome": "found", "steps": 2, "tapped_none_of_these": False},
        {"outcome": "found", "steps": 3, "tapped_none_of_these": False},
        {"outcome": "abandoned", "steps": 4, "tapped_none_of_these": True},
    ]

    assert compute_found_in_k(sessions, k=3) == 2 / 3
    assert compute_mean_steps(sessions) == 2.5
    assert compute_none_of_these_rate(sessions) == 1 / 3


def test_ece_computation():
    """Verify ECE calculation on calibrated and uncalibrated probabilities."""
    confidences = [0.8, 0.7, 0.2, 0.1]
    labels = [1, 1, 0, 0]
    ece = compute_ece(confidences, labels)
    assert 0.0 <= ece <= 0.5


def test_calibration_training():
    """Verify isotonic regression calibrator can fit and predict."""
    raw = [0.1, 0.3, 0.5, 0.7, 0.9]
    labels = [0, 0, 1, 1, 1]
    calibrator = train_calibrator(raw, labels)
    pred = calibrate_score(0.6, calibrator)
    assert 0.0 <= pred <= 1.0


def test_baselines():
    """Verify baselines produce valid comparison benchmarks."""
    b1 = run_baseline_b1_scroll(500)
    assert b1["expected_seconds"] > 0
    assert b1["success_rate"] == 0.80

    b2 = run_baseline_b2_text_query(500)
    assert b2["success_rate"] == 0.35
