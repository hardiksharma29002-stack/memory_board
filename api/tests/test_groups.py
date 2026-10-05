"""Tests for group building and candidate clustering."""

from sqlmodel import Session
from api.app.models import Photo, PhotoTag
from api.app.engine.groups import build_candidate_groups


def setup_photos_and_tags(session: Session, count=25):
    """Seed test photos with tags."""
    for i in range(count):
        pid = f"photo_{i}"
        photo = Photo(id=pid, path=f"data/photos/{pid}.jpg", width=400, height=300)
        session.add(photo)

        # Assign food and celebration tags to first half, outdoors to second half
        if i < 15:
            session.add(PhotoTag(photo_id=pid, cue_id="scene_food_stall", score=0.85))
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_warm_yellow", score=0.75))
        else:
            session.add(PhotoTag(photo_id=pid, cue_id="setting_outdoors", score=0.9))
            session.add(PhotoTag(photo_id=pid, cue_id="lighting_bright_daylight", score=0.8))

    session.commit()


def test_build_candidate_groups(session):
    """Verify group builder returns groups with why chips and confidence."""
    setup_photos_and_tags(session, count=25)

    groups = build_candidate_groups(
        positive_cues=["scene_food_stall", "lighting_warm_yellow"],
        target_engine=session.bind,
    )

    assert len(groups) >= 1
    assert len(groups) <= 3

    # Check structure
    top_group = groups[0]
    assert "id" in top_group
    assert "label" in top_group
    assert "confidence" in top_group
    assert top_group["confidence"]["band"] in ("highest", "good", "possible", "unsure")
    assert len(top_group["photos"]) >= 1

    # Verify sorted by confidence descending
    for i in range(len(groups) - 1):
        assert groups[i]["confidence"]["calibrated"] >= groups[i + 1]["confidence"]["calibrated"]


def test_macro_album_title_deduplication(session):
    """Verify that macro albums generated have distinct, non-repetitive titles."""
    setup_photos_and_tags(session, count=30)
    groups = build_candidate_groups(
        positive_cues=["scene_food_stall", "lighting_warm_yellow"],
        target_engine=session.bind,
    )
    labels = [g["label"].lower().strip() for g in groups]
    assert len(labels) == len(set(labels)), "All macro album labels must be unique"
    for label in labels:
        assert "puja" not in label or "celebration" in label or "ritual" in label, "No generic static labels"
