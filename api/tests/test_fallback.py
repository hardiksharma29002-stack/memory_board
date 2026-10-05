"""Tests for no-dead-end fallback ladder."""

from api.app.engine.session import create_session, add_clue
from api.app.engine.fallback import resolve_fallback


def test_fallback_ladder_level_1(session):
    """Multiple clues -> relax the weakest/most recently added clue."""
    sess = create_session(entry="search_pill", db=session)
    add_clue(sess, clue_type="cue", label="Outdoors", value="setting_outdoors", db=session)
    add_clue(sess, clue_type="almost", label="Night", value="lighting_night_dark", db=session)

    res = resolve_fallback(sess)
    assert res.level == 1
    assert "relaxed" in res.message.lower()
    assert len(res.relaxed_clue_ids) == 1
    # Almost has weight 0.7 vs cue 1.0, so the almost clue is weakest
    assert res.relaxed_clue_ids[0] == sess.clues[1].id


def test_fallback_ladder_level_2(session):
    """Single clue -> propose a clarifying question."""
    sess = create_session(entry="search_pill", db=session)
    add_clue(sess, clue_type="cue", label="Outdoors", value="setting_outdoors", db=session)

    res = resolve_fallback(sess)
    assert res.level == 2
    assert res.suggested_question_id is not None


def test_fallback_ladder_level_3(session):
    """Zero clues -> jump to recent timeline."""
    sess = create_session(entry="search_pill", db=session)
    res = resolve_fallback(sess)
    assert res.level == 3
    assert res.timeline_jump_date is not None
