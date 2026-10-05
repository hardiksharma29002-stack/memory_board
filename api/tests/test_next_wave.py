"""Tests for Phase 7 (v1.1) Next-Wave features."""

import json
from sqlmodel import Session
from api.app.models import Photo
from api.app.engine.next_wave import (
    check_hiding_places,
    get_who_was_there_options,
    match_paint_it_palette,
    segment_timeline_moments,
)


def test_hiding_places(client, session: Session):
    """Verify hiding places checks trash, archived, locked, and unbacked up."""
    p_trash = Photo(id="hp_trash", path="data/photos/1.jpg", in_trash=1)
    p_arch = Photo(id="hp_arch", path="data/photos/2.jpg", archived=1)
    p_lock = Photo(id="hp_lock", path="data/photos/3.jpg", locked=1)
    p_unback = Photo(id="hp_unback", path="data/photos/4.jpg", backed_up=0)
    p_normal = Photo(id="hp_normal", path="data/photos/5.jpg", backed_up=1)

    session.add_all([p_trash, p_arch, p_lock, p_unback, p_normal])
    session.commit()

    # Via engine
    hp = check_hiding_places(target_engine=session.bind)
    assert hp["trash"]["count"] == 1
    assert hp["archive"]["count"] == 1
    assert hp["locked"]["count"] == 1
    assert hp["unbacked"]["count"] == 1
    assert "hp_trash" in hp["trash"]["photo_ids"]

    # Via API endpoint
    res = client.get("/api/session/features/hiding-places")
    assert res.status_code == 200
    data = res.json()
    assert data["trash"]["count"] == 1


def test_paint_it_palette_matching(client, session: Session):
    """Verify paint-it matches photos by color palette distance."""
    # Photo with red palette
    p_red = Photo(
        id="p_red",
        path="data/photos/red.jpg",
        palette=json.dumps(["#FF0000", "#EE1111", "#CC0000"]),
        hour_bucket=14,
    )
    # Photo with blue palette
    p_blue = Photo(
        id="p_blue",
        path="data/photos/blue.jpg",
        palette=json.dumps(["#0000FF", "#1111EE", "#0000CC"]),
        hour_bucket=14,
    )
    session.add_all([p_red, p_blue])
    session.commit()

    # Match red target
    matched = match_paint_it_palette(["#FF0000"], day_night="day", target_engine=session.bind)
    assert len(matched) == 2
    assert matched[0]["id"] == "p_red"

    # Via API endpoint
    res = client.post("/api/session/features/paint-it", json={"colors": ["#0000FF"], "day_night": "day"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["photos"]) >= 1
    assert data["photos"][0]["id"] == "p_blue"


def test_who_was_there_options(session: Session):
    """Verify face count co-occurrence produces privacy-preserving count buckets."""
    photos = [
        Photo(id="wt_solo", path="1.jpg", face_count=1),
        Photo(id="wt_duo", path="2.jpg", face_count=2),
        Photo(id="wt_grp", path="3.jpg", face_count=4),
        Photo(id="wt_crowd", path="4.jpg", face_count=8),
    ]
    session.add_all(photos)
    session.commit()

    options = get_who_was_there_options([p.id for p in photos], target_engine=session.bind)
    assert len(options) == 4
    opt_map = {o["id"]: o["count"] for o in options}
    assert opt_map["people_just_me"] == 1
    assert opt_map["people_2_people"] == 1
    assert opt_map["people_3_5_people"] == 1
    assert opt_map["people_big_crowd"] == 1


def test_timeline_moments_segmentation(session: Session):
    """Verify timeline photos are segmented into moments when gap > 6h."""
    p1 = Photo(id="m1", path="1.jpg", taken_at="2026-10-01T10:00:00")
    p2 = Photo(id="m2", path="2.jpg", taken_at="2026-10-01T11:00:00")
    # 24h gap
    p3 = Photo(id="m3", path="3.jpg", taken_at="2026-10-02T12:00:00")

    session.add_all([p1, p2, p3])
    session.commit()

    moments = segment_timeline_moments(target_engine=session.bind, gap_hours=6.0)
    assert len(moments) == 2
    assert moments[0]["photo_count"] == 2
    assert moments[1]["photo_count"] == 1
