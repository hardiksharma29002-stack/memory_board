"""Comprehensive automated verification suite for all edge cases."""

import io
import time
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from api.app.main import app
from api.app.config import PHOTOS_DIR, THUMBS_DIR
from api.app.database import engine
from api.app.models import Photo
from api.app.engine.memory_ai import parse_vague_memory_to_clues
from api.app.engine.groups import build_candidate_groups
from api.app.vocab import CUE_LOOKUP

client = TestClient(app)

def test_1_health_and_config():
    print("\n--- Test 1: Health & Config ---")
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    print("Health response:", data)
    assert data["status"] == "ok"
    assert data["photos_indexed"] > 0
    print("✓ Test 1 passed!")


def test_2_thumbnail_resilience():
    print("\n--- Test 2: Thumbnail & Image Serving Resilience ---")
    # 1. Existing thumbnail
    with Session(engine) as db:
        first_photo = db.exec(select(Photo)).first()
        assert first_photo is not None
        pid = first_photo.id

    r_exist = client.get(f"/thumbs/{pid}_256.webp")
    assert r_exist.status_code == 200
    print(f"Existing thumb {pid}_256.webp: status={r_exist.status_code}, content_type={r_exist.headers.get('content-type')}")

    # 2. Nonexistent thumbnail (should NEVER 404, returns SVG placeholder or dynamic gen)
    r_fake = client.get("/thumbs/0000000000000000_256.webp")
    assert r_fake.status_code == 200
    print(f"Nonexistent thumb: status={r_fake.status_code}, content_type={r_fake.headers.get('content-type')}")
    assert "image" in r_fake.headers.get("content-type", "")

    # 3. Dedicated API thumb endpoint
    r_api_thumb = client.get(f"/api/photos/{pid}/thumb?size=256")
    assert r_api_thumb.status_code == 200
    print(f"API thumb endpoint: status={r_api_thumb.status_code}")

    # 4. Dedicated API raw photo endpoint
    r_api_raw = client.get(f"/api/photos/{pid}/raw")
    assert r_api_raw.status_code == 200
    print(f"API raw endpoint: status={r_api_raw.status_code}")
    print("✓ Test 2 passed!")


def test_3_photo_upload_guaranteed():
    print("\n--- Test 3: Guaranteed Photo Upload & Indexing ---")
    # Create test image in memory (PNG, RGB, 100x100)
    img_byte_arr = io.BytesIO()
    test_img = Image.new("RGB", (320, 240), color=(140, 20, 210))
    test_img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    filename = f"test_purple_cake_{int(time.time())}.PNG"
    files = [("files", (filename, img_byte_arr.getvalue(), "image/png"))]

    res = client.post("/api/photos/upload", files=files, data={"replace": "false"})
    print("Upload status:", res.status_code, res.json())
    assert res.status_code == 200
    data = res.json()
    assert data["uploaded_count"] == 1
    assert data["total_photos"] > 0

    # Verify photo was added to database and thumbnails generated
    with Session(engine) as db:
        newest_photo = db.exec(select(Photo).order_by(Photo.id.desc())).first()
        assert newest_photo is not None
        print(f"Newly indexed photo ID: {newest_photo.id}")
        t_check = client.get(f"/thumbs/{newest_photo.id}_256.webp")
        assert t_check.status_code == 200

    print("✓ Test 3 passed!")


def test_4_ai_vague_memory_understanding():
    print("\n--- Test 4: AI Vague Memory Parsing ---")
    test_queries = [
        "dark night dinner with a small group of friends eating biryani",
        "bright sunny morning walk in green park alone",
        "sunset at the beach with my friend",
        "cafe with masala dosa and chai",
    ]

    for q in test_queries:
        clues = parse_vague_memory_to_clues(q)
        print(f"Query: '{q}' => Clues: {clues}")
        assert len(clues) > 0
        for c in clues:
            assert c["cue_id"] in CUE_LOOKUP or c["cue_id"].startswith("custom_")
            print(f"   ✓ Clue '{c['label']}' -> cue_id: {c['cue_id']}")

    print("✓ Test 4 passed!")


def test_5_groups_and_clustering():
    print("\n--- Test 5: Candidate Groups & Clustering ---")
    # Test with cafe / restaurant cue
    groups = build_candidate_groups(positive_cues=["setting_food_place", "scene_food_stall"])
    print(f"Generated {len(groups)} macro album groups for setting_food_place:")
    assert len(groups) > 0
    for g in groups:
        print(f"   Album: {g['id']} | label: '{g['label']}' | confidence: {g['confidence']['percentage']}% | photos: {len(g['photos'])}")
        # Check first 3 photos in each group
        for p in g["photos"][:3]:
            res = client.get(p["thumb_256"])
            assert res.status_code == 200
            assert "image" in res.headers.get("content-type", "")

    # Edge case: positive cues that match very few or 0 photos
    sparse_groups = build_candidate_groups(positive_cues=["nonexistent_cue_xyz"])
    print(f"Sparse/empty cue groups returned: {len(sparse_groups)}")
    # Should not crash!

    print("✓ Test 5 passed!")


def test_6_full_session_flow():
    print("\n--- Test 6: Full Search Session Lifecycle ---")
    # Start session
    s_start = client.post("/api/session", json={"entry": "search_pill", "initial_query": "cafe dinner"})
    assert s_start.status_code == 200
    s_data = s_start.json()
    sid = s_data["session_id"]
    print(f"Started session {sid}, initial clues: {len(s_data.get('initial_clues', []))}")

    # Add cue
    s_cues = client.post(f"/api/session/{sid}/cues", json={"cue_ids": ["setting_food_place"]})
    assert s_cues.status_code == 200
    assert len(s_cues.json()["groups"]) > 0

    # Trigger Almost
    first_group = s_cues.json()["groups"][0]
    sample_pid = first_group["photos"][0]["id"]
    s_almost = client.post(f"/api/session/{sid}/almost", json={"photo_id": sample_pid, "difference_axis": "diff_look"})
    assert s_almost.status_code == 200
    assert len(s_almost.json()["photos"]) > 0

    # Trigger Fallback
    s_fallback = client.post(f"/api/session/{sid}/fallback")
    assert s_fallback.status_code == 200
    print("Fallback level:", s_fallback.json().get("level"), "message:", s_fallback.json().get("message"))

    # Rewind
    s_rewind = client.post(f"/api/session/{sid}/rewind")
    assert s_rewind.status_code == 200

    print("✓ Test 6 passed!")


if __name__ == "__main__":
    print("Running Full Edge Case Test Suite...")
    test_1_health_and_config()
    test_2_thumbnail_resilience()
    test_3_photo_upload_guaranteed()
    test_4_ai_vague_memory_understanding()
    test_5_groups_and_clustering()
    test_6_full_session_flow()
    print("\n==========================================")
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! ZERO FAILURES!")
    print("==========================================")
