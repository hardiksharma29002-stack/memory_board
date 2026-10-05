"""Tests for information-gain question selection."""

from sqlmodel import Session
from api.app.models import Photo, PhotoTag
from api.app.vocab import QUESTIONS
from api.app.engine.questions import compute_entropy, select_best_question


def test_compute_entropy():
    """Verify Shannon entropy calculation."""
    # Uniform across 4 options: H = - 4 * (0.25 * log2(0.25)) = 2.0 bits
    uniform_4 = [0.25, 0.25, 0.25, 0.25]
    assert abs(compute_entropy(uniform_4) - 2.0) < 1e-4

    # Degenerate case (100% on one option): H = 0 bits
    single_choice = [1.0, 0.0, 0.0, 0.0]
    assert abs(compute_entropy(single_choice) - 0.0) < 1e-4


def test_select_best_question_empty_candidates(session: Session):
    """When candidates are empty, returns the first unasked question."""
    q = select_best_question(
        candidate_photo_ids=[],
        asked_question_ids=[],
        target_engine=session.bind,
    )
    assert q is not None
    assert q.id == QUESTIONS[0].id

    # If first is asked, returns next
    q2 = select_best_question(
        candidate_photo_ids=[],
        asked_question_ids=[QUESTIONS[0].id],
        target_engine=session.bind,
    )
    assert q2 is not None
    assert q2.id == QUESTIONS[1].id


def test_select_best_question_with_candidates(session: Session):
    """Seed candidate photos and verify question selection works."""
    for i in range(10):
        pid = f"q_photo_{i}"
        session.add(Photo(id=pid, path=f"data/photos/{pid}.jpg"))
        # 5 morning, 5 night
        if i < 5:
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_bright_daylight", score=0.9))
        else:
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_night_dark", score=0.9))
    session.commit()

    candidate_ids = [f"q_photo_{i}" for i in range(10)]
    q = select_best_question(
        candidate_photo_ids=candidate_ids,
        asked_question_ids=[],
        target_engine=session.bind,
    )
    assert q is not None
    assert len(q.options) >= 4


def test_cant_recall_option_preserves_candidates(session: Session):
    """Verify selecting 'cant_recall' does not crash and continues questioning."""
    candidate_ids = [f"q_photo_{i}" for i in range(10)]
    q = select_best_question(
        candidate_photo_ids=candidate_ids,
        asked_question_ids=["time_of_day"],
        target_engine=session.bind,
    )
    assert q is not None
    assert q.id != "time_of_day"
    assert len(q.options) >= 3

