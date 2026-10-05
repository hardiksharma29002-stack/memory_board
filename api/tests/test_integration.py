"""Full integration tests covering complete API flows."""

from sqlmodel import Session
from api.app.models import Photo, PhotoTag


def seed_database(session: Session):
    """Seed test photos for integration tests."""
    for i in range(15):
        pid = f"integ_photo_{i}"
        photo = Photo(
            id=pid,
            path=f"data/photos/{pid}.jpg",
            hour_bucket=14 if i < 8 else 22,
            face_count=1 if i < 5 else (2 if i < 10 else 4),
            width=800,
            height=600,
        )
        session.add(photo)

        if i < 8:
            session.add(PhotoTag(photo_id=pid, cue_id="scene_celebration", score=0.85))
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_warm_yellow", score=0.75))
        else:
            session.add(PhotoTag(photo_id=pid, cue_id="setting_outdoors", score=0.9))
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_night_dark", score=0.8))

    session.commit()


def test_full_search_and_answer_flow(client, session):
    """Test start session -> answer question -> view groups -> pivot almost -> found."""
    seed_database(session)

    # 1. Start session
    start_resp = client.post("/api/session", json={"entry": "search_pill"})
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session_id"]

    # 2. Answer question
    ans_resp = client.post(
        f"/api/session/{sess_id}/answer",
        json={"question_id": "q_time", "option_id": "opt_evening"},
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert ans_data["step"] in ("question", "groups")

    # 3. Select cues
    cue_resp = client.post(
        f"/api/session/{sess_id}/cues",
        json={"cue_ids": ["scene_celebration"]},
    )
    assert cue_resp.status_code == 200
    cue_data = cue_resp.json()
    assert cue_data["step"] == "groups"
    assert "groups" in cue_data
    assert len(cue_data["groups"]) >= 1

    # 4. Pivot with Almost!
    almost_resp = client.post(
        f"/api/session/{sess_id}/almost",
        json={"photo_id": "integ_photo_0", "difference_axis": "diff_time"},
    )
    assert almost_resp.status_code == 200
    almost_data = almost_resp.json()
    assert almost_data["step"] == "almost"
    assert "photos" in almost_data

    # 5. Fallback ladder
    fallback_resp = client.post(f"/api/session/{sess_id}/fallback")
    assert fallback_resp.status_code == 200
    fb_data = fallback_resp.json()
    assert fb_data["step"] == "fallback"
    assert fb_data["level"] >= 1

    # 6. Complete found
    found_resp = client.post(
        f"/api/session/{sess_id}/found",
        json={"photo_id": "integ_photo_0"},
    )
    assert found_resp.status_code == 200
    assert found_resp.json()["outcome"] == "found"
