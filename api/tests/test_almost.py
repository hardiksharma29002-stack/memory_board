"""Tests for 'Almost!' nearest-neighbor pivot engine."""

from sqlmodel import Session
from api.app.models import Photo
from api.app.engine.almost import pivot_almost


def test_pivot_almost_diff_time(session: Session):
    """Verify almost pivot with diff_time prefers photos with different hour_bucket."""
    anchor = Photo(id="anchor_1", path="data/photos/anchor.jpg", hour_bucket=12)
    night_photo = Photo(id="p_night", path="data/photos/night.jpg", hour_bucket=23)
    noon_photo = Photo(id="p_noon", path="data/photos/noon.jpg", hour_bucket=13)

    session.add_all([anchor, night_photo, noon_photo])
    session.commit()

    results = pivot_almost(
        photo_id="anchor_1",
        difference_axis="diff_time",
        target_engine=session.bind,
    )
    assert len(results) == 2
    # Night photo has greater hour difference (23 - 12 = 11) than noon (13 - 12 = 1)
    assert results[0]["id"] == "p_night"


def test_pivot_almost_diff_people(session: Session):
    """Verify almost pivot with diff_people prefers photos with different face_count."""
    anchor = Photo(id="anchor_2", path="data/photos/anchor2.jpg", face_count=1)
    crowd_photo = Photo(id="p_crowd", path="data/photos/crowd.jpg", face_count=6)
    solo_photo = Photo(id="p_solo", path="data/photos/solo.jpg", face_count=1)

    session.add_all([anchor, crowd_photo, solo_photo])
    session.commit()

    results = pivot_almost(
        photo_id="anchor_2",
        difference_axis="diff_people",
        target_engine=session.bind,
    )
    assert len(results) == 2
    assert results[0]["id"] == "p_crowd"
