"""Tests for cue vocabulary and question bank."""

from api.app.vocab import CUES, CUES_BY_GROUP, QUESTIONS, ALMOST_OPTIONS


def test_cue_vocabulary_groups():
    """Verify all 5 cognitive groups are represented."""
    expected_groups = {"lighting", "setting", "scene", "people", "color"}
    actual_groups = set(CUES_BY_GROUP.keys())
    assert expected_groups.issubset(actual_groups)
    assert len(CUES) >= 30


def test_question_bank():
    """Verify each question has 4 distinct options."""
    assert len(QUESTIONS) >= 7
    for q in QUESTIONS:
        assert len(q.options) == 4
        opt_ids = [opt.id for opt in q.options]
        assert len(opt_ids) == len(set(opt_ids))


def test_almost_options():
    """Verify Almost options have 5 choices."""
    assert len(ALMOST_OPTIONS) == 5
