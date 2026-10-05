"""Tests for configuration loading and system integrity."""

from pathlib import Path
from api.app.config import load_config, CONFIG_PATH, CONFIG
from api.app.models import Photo, PhotoTag, PhotoActivity, Session, Event


def test_config_loads_from_yaml():
    """Verify that config loads from YAML with correct types and non-null values."""
    assert CONFIG_PATH.exists()
    cfg = load_config(CONFIG_PATH)

    # Board settings
    assert cfg.board.cards_min >= 3
    assert cfg.board.cards_max <= 6
    assert 0.0 < cfg.board.min_support < cfg.board.max_support < 1.0

    # Confidence settings
    assert cfg.confidence.bands.highest > cfg.confidence.bands.good > cfg.confidence.bands.possible
    assert sum([
        cfg.confidence.w_match,
        cfg.confidence.w_exclusion,
        cfg.confidence.w_tight,
        cfg.confidence.w_prior
    ]) == 1.0

    # Questions settings
    assert cfg.questions.max_questions == 3
    assert cfg.questions.min_gain_bits > 0


def test_health_endpoint(client):
    """Verify the /api/health endpoint responds correctly."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["config_loaded"] is True
    assert isinstance(data["photos_indexed"], int)


def test_database_models_can_persist(session):
    """Verify all 5 database models can be inserted and queried."""
    photo = Photo(id="p1", path="data/photos/test.jpg", width=800, height=600)
    session.add(photo)

    tag = PhotoTag(photo_id="p1", cue_id="food_chai", score=0.85)
    session.add(tag)

    activity = PhotoActivity(photo_id="p1", opens=2, shares=1)
    session.add(activity)

    sess = Session(id="s1", started_at="2026-10-05T12:00:00Z", entry="search_pill")
    session.add(sess)

    evt = Event(session_id="s1", name="session_started", ts="2026-10-05T12:00:00Z")
    session.add(evt)

    session.commit()

    retrieved_photo = session.get(Photo, "p1")
    assert retrieved_photo is not None
    assert retrieved_photo.width == 800

    retrieved_sess = session.get(Session, "s1")
    assert retrieved_sess is not None
    assert retrieved_sess.entry == "search_pill"
