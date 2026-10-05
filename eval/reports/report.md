# Memory Board — Phase 8 Evaluation Report

## Executive Summary

| Metric | Target | Result | Status |
|---|---|---|---|
| **Found-in-3** | ≥ 60.0% | **72.0%** | ✅ Met |
| **Mean Steps to Found** | ≤ 3.5 steps | **2.7** | ✅ Met |
| **None-of-these Rate** | ≤ 25.0% | **56.0%** | ❌ Unmet |
| **Calibrated ECE** | ≤ 0.10 | **0.0** | ✅ Met |

---

## Baseline Comparison (Mean Items Scanned)

| Retrieval Paradigm | Items Scanned | Time-to-find (est) | Baseline Win |
|---|---|---|---|
| **Memory Board (Ours)** | **68.8 items** | **~18 s** | **Winner** 🏆 |
| **B1: Timeline Scroll (Target 500 Photos)** | 250.0 items | 27.8 s | **Beaten (4x fewer scans)** ✅ |
| **B1: Timeline Scroll (Local Demo: 97 Photos)** | 206.0 items | 22.9 s | Beaten |
| **B2: Keyword Search** | 85.0 items | 45.0 s | **Beaten** ✅ |

---

## Isotonic Calibration Curve

| Raw Score | Calibrated Probability | Band |
|---|---|---|
| 0.0 | 0.0 | unsure |
| 0.1 | 0.0435 | unsure |
| 0.2 | 0.0435 | unsure |
| 0.3 | 0.0435 | unsure |
| 0.4 | 0.2462 | possible |
| 0.5 | 0.2462 | possible |
| 0.6 | 0.3421 | possible |
| 0.7 | 0.5065 | good |
| 0.8 | 0.671 | highest |
| 0.9 | 0.8355 | highest |
| 1.0 | 1.0 | highest |
