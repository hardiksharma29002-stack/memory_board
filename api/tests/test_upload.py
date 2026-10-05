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
