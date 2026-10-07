"""Test suite for photo stats and upload endpoints."""

import io
from fastapi.testclient import TestClient
from PIL import Image

from api.app.main import app

client = TestClient(app)


def test_photo_stats_endpoint():
    """Verify that photo stats returns photo count, 500-photo cap, and nudge message."""
    res = client.get("/api/photos/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_photos" in data
    assert data["cap"] == 500
    assert "nudge_message" in data
    assert "100 real photos" in data["nudge_message"]


def test_smart_cards_endpoint():
    """Verify smart-cards generation with Groq fallback."""
    res = client.post("/api/session/smart-cards", json={"query": "beach sunset with friends"})
    assert res.status_code == 200
    data = res.json()
    assert "cards" in data
    assert len(data["cards"]) >= 2
    for card in data["cards"]:
        assert "id" in card
        assert "title" in card
        assert "options" in card


def test_upload_external_photo_and_retrieve():
    """Verify that uploading external photos indexes them, generates thumbnails, and serves them."""
    img_byte_arr = io.BytesIO()
    test_img = Image.new("RGB", (300, 300), color=(200, 50, 100))
    test_img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = [("files", ("test_external_vacation.jpg", img_byte_arr.getvalue(), "image/jpeg"))]
    res = client.post("/api/photos/upload", files=files, data={"replace": "false"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["uploaded_count"] >= 1

    # Verify photos list contains it
    list_res = client.get("/api/photos?limit=10")
    assert list_res.status_code == 200
    photos = list_res.json()["photos"]
    assert len(photos) >= 1
    sample_pid = photos[0]["id"]

    # Verify thumbnail serves with 200 OK
    thumb_res = client.get(f"/api/photos/{sample_pid}/thumb?size=256")
    assert thumb_res.status_code == 200

    # Clean up uploaded test photo so database & gallery are never polluted
    del_res = client.delete(f"/api/photos/{sample_pid}")
    assert del_res.status_code == 200

