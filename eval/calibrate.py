"""Isotonic regression calibration for confidence estimates."""

import numpy as np
from sklearn.isotonic import IsotonicRegression
from typing import List, Tuple, Dict


def train_calibrator(raw_scores: List[float], labels: List[int]) -> IsotonicRegression:
    """Fit an isotonic regression model mapping raw confidence scores to empirical probabilities."""
    ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    # Anchor extreme boundary points so 0 maps to 0 and 1 maps to 1
    X = np.array([0.0] + list(raw_scores) + [1.0])
    y = np.array([0.0] + list(labels) + [1.0])
    ir.fit(X, y)
    return ir


def calibrate_score(raw_score: float, calibrator: IsotonicRegression) -> float:
    """Apply isotonic calibration to a raw score."""
    res = calibrator.predict([raw_score])
    return float(np.clip(res[0], 0.0, 1.0))
