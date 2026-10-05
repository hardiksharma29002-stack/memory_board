"""Tests for activity and telemetry events API endpoints."""

from sqlmodel import Session, select
from api.app.models import Photo, PhotoActivity, Event


def test_activity_endpoint(client, session: Session):
    """Verify POST /api/activity properly records opens, shares, and favorites."""
    photo = Photo(id="act_p1", path="data/photos/test.jpg")
    session.add(photo)
    session.commit()

    # 1. Record open
    res = client.post("/api/activity", json={"photo_id": "act_p1", "kind": "open"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["opens"] == 1
    assert data["last_opened_at"] is not None

    # 2. Record share
    res = client.post("/api/activity", json={"photo_id": "act_p1", "kind": "share"})
    assert res.status_code == 200
    assert res.json()["shares"] == 1

    # 3. Record favorite (toggle on)
    res = client.post("/api/activity", json={"photo_id": "act_p1", "kind": "favorite"})
    assert res.status_code == 200
    assert res.json()["favorite"] == 1

    # 4. Check DB
    db_act = session.get(PhotoActivity, "act_p1")
    assert db_act.opens == 1
    assert db_act.shares == 1
    assert db_act.favorite == 1


def test_events_batch_endpoint(client, session: Session):
    """Verify POST /api/events properly batch-stores telemetry events."""
    payload = {
        "events": [
            {
                "session_id": "sim_sess_1",
                "name": "board_shown",
                "payload": {"cue_ids": ["c1", "c2"], "render_ms": 120},
            },
            {
                "session_id": "sim_sess_1",
                "name": "found",
                "payload": {"photo_id": "act_p1", "steps": 2},
            },
        ]
    }
    res = client.post("/api/events", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["recorded"] == 2

    # Query DB
    records = session.exec(select(Event).where(Event.session_id == "sim_sess_1")).all()
    assert len(records) == 2
    names = {r.name for r in records}
    assert "board_shown" in names
    assert "found" in names
