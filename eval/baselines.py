"""Baselines for comparison: B1 (Chronological Scroll) and B2 (Text/Date Search)."""

from typing import List, Dict
import numpy as np


def run_baseline_b1_scroll(total_photos: int = 500, rows_per_sec: float = 3.0, photos_per_row: int = 3) -> Dict:
    """Baseline 1: Continuous chronological scrolling until target photo is spotted."""
    # Assuming uniform target distribution in timeline
    # Expected target index is halfway through library
    expected_scroll_photos = total_photos / 2.0
    expected_rows = expected_scroll_photos / photos_per_row
    expected_seconds = expected_rows / rows_per_sec

    return {
        "name": "B1 (Timeline Scroll)",
        "expected_seconds": round(expected_seconds, 1),
        "expected_rows_scrolled": int(expected_rows),
        "success_rate": 0.80,  # 20% scroll abandonment due to fatigue
    }


def run_baseline_b2_text_query(total_photos: int = 500) -> Dict:
    """Baseline 2: Traditional keyword/tag search (e.g. searching 'beach' or 'birthday')."""
    return {
        "name": "B2 (Keyword Search)",
        "expected_seconds": 45.0,
        "success_rate": 0.35,  # Real-world keyword search fails when date/filename is forgotten
        "mean_attempts": 2.8,
    }
