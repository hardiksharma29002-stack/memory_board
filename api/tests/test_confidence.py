"""Tests for Confidence Engine (monotonicity, bands, tie-breaking, no-ops)."""

from api.app.engine.confidence import compute_confidence, apply_tie_breaking


def test_confidence_zero_clues_is_unsure():
    """Verify that zero clues always produces 'unsure' band."""
    conf = compute_confidence(
        group_photo_ids=["p1", "p2", "p3"],
        positive_cues=[],
        negative_cues=[],
        photo_tags_lookup={},
    )
    assert conf.band == "unsure"
    assert conf.calibrated == 0.0


def test_confidence_monotonicity_in_positive_clues():
    """Verify that adding matching clues increases confidence monotonically."""
    tags = {
        "p1": {"cue_a": 0.9, "cue_b": 0.85, "cue_c": 0.8},
        "p2": {"cue_a": 0.85, "cue_b": 0.8, "cue_c": 0.75},
        "p3": {"cue_a": 0.8, "cue_b": 0.75, "cue_c": 0.7},
    }

    # 1 clue
    conf_1 = compute_confidence(
        group_photo_ids=["p1", "p2", "p3"],
        positive_cues=["cue_a"],
        negative_cues=[],
        photo_tags_lookup=tags,
    )

    # 2 clues
    conf_2 = compute_confidence(
        group_photo_ids=["p1", "p2", "p3"],
        positive_cues=["cue_a", "cue_b"],
        negative_cues=[],
        photo_tags_lookup=tags,
    )

    # 3 clues
    conf_3 = compute_confidence(
        group_photo_ids=["p1", "p2", "p3"],
        positive_cues=["cue_a", "cue_b", "cue_c"],
        negative_cues=[],
        photo_tags_lookup=tags,
    )

    assert conf_2.calibrated >= conf_1.calibrated
    assert conf_3.calibrated >= conf_2.calibrated


def test_tie_breaking_rule():
    """Verify tie rule: two groups within 0.05 both get 'good' band."""
    groups = [
        {"confidence": {"calibrated": 0.65, "band": "highest", "band_label": "Highest chance"}},
        {"confidence": {"calibrated": 0.62, "band": "good", "band_label": "Good chance"}},
    ]
    apply_tie_breaking(groups)
    assert groups[0]["confidence"]["band"] == "good"
    assert groups[1]["confidence"]["band"] == "good"
