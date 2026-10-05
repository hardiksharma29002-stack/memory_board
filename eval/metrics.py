"""Evaluation metrics for Memory Board prototype."""

from typing import List, Dict, Tuple
import numpy as np


def compute_found_in_k(sessions: List[Dict], k: int = 3) -> float:
    """Compute percentage of sessions where target was found within k steps. Target: >= 60%."""
    if not sessions:
        return 0.0
    success = sum(1 for s in sessions if s.get("outcome") == "found" and s.get("steps", 999) <= k)
    return success / len(sessions)


def compute_mean_steps(sessions: List[Dict]) -> float:
    """Compute mean steps taken for successful retrieval sessions."""
    found_sessions = [s for s in sessions if s.get("outcome") == "found"]
    if not found_sessions:
        return 0.0
    return float(np.mean([s.get("steps", 0) for s in found_sessions]))


def compute_none_of_these_rate(sessions: List[Dict]) -> float:
    """Compute percentage of sessions that tapped 'None of these'. Target: <= 25%."""
    if not sessions:
        return 0.0
    none_count = sum(1 for s in sessions if s.get("tapped_none_of_these", False))
    return none_count / len(sessions)


def compute_ece(confidences: List[float], labels: List[int], n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE). Target: <= 0.10.

    ECE = Σ (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    if not confidences or not labels or len(confidences) != len(labels):
        return 0.0

    conf_arr = np.array(confidences)
    label_arr = np.array(labels)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(conf_arr)

    for i in range(n_bins):
        in_bin = (conf_arr > bin_boundaries[i]) & (conf_arr <= bin_boundaries[i + 1])
        bin_size = np.sum(in_bin)
        if bin_size > 0:
            avg_conf = np.mean(conf_arr[in_bin])
            avg_acc = np.mean(label_arr[in_bin])
            ece += (bin_size / n) * abs(avg_acc - avg_conf)

    return float(ece)
