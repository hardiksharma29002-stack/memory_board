"""Tests for Cue Board generation and session state endpoints."""

from sqlmodel import Session
from api.app.models import Photo, PhotoTag
from api.app.engine.cue_board import generate_cue_cards
from api.app.engine.session import (
    create_session,
    add_clue,
    rewind_session,
    complete_session,
)


def populate_dummy_photo_tags(session: Session, count=20):
    """Populate test photos and tags."""
    cues = ["lighting_warm_yellow", "setting_indoors", "scene_celebration", "color_warm"]
    for i in range(count):
        pid = f"photo_{i}"
        photo = Photo(id=pid, path=f"data/photos/{pid}.jpg", width=400, height=300)
        session.add(photo)

        # Assign 2 cues to each photo
        assigned_cues = [cues[i % len(cues)], cues[(i + 1) % len(cues)]]
        for c in assigned_cues:
            tag = PhotoTag(photo_id=pid, cue_id=c, score=0.8)
            session.add(tag)
    session.commit()


def test_cue_cards_generation(session):
    """Verify cue cards are generated with labels, previews, and palettes."""
    populate_dummy_photo_tags(session, count=20)
    cards = generate_cue_cards(target_engine=session.bind)

    assert len(cards) >= 1
    assert len(cards) <= 5
    for c in cards:
        assert c.cue_id
        assert c.label
        assert c.photo_count > 0
        assert len(c.palette) == 3


def test_session_api_flow(client, session):
    """Test full session API lifecycle: create -> cues -> none -> rewind -> found."""
    populate_dummy_photo_tags(session, count=10)

    # 1. Start session
    resp = client.post("/api/session", json={"entry": "search_pill"})
    assert resp.status_code == 200
    data = resp.json()
    sess_id = data["session_id"]
    assert data["step"] == "cue_board"
    assert "cards" in data

    # 2. Add cue
    resp = client.post(f"/api/session/{sess_id}/cues", json={"cue_ids": ["lighting_warm_yellow"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] == "groups"
    assert len(data["clues"]) == 1
    assert data["clues"][0]["value"] == "lighting_warm_yellow"

    # 3. None of these
    resp = client.post(f"/api/session/{sess_id}/none")
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] == "question"
    assert "question" in data
    assert len(data["question"]["options"]) == 4

    # 4. Rewind
    resp = client.post(f"/api/session/{sess_id}/rewind")
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] == "groups"

    # 5. Mark found
    resp = client.post(f"/api/session/{sess_id}/found", json={"photo_id": "photo_0"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["outcome"] == "found"
