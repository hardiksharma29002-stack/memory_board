"""Tests for cognitive memory AI, non-pictorial cards, 4 macro albums, and context-preserving fallback."""

import pytest
from fastapi.testclient import TestClient
from api.app.main import app
from api.app.engine.memory_ai import (
    parse_vague_memory_to_clues,
    generate_cognitive_cue_cards,
    generate_followup_memory_probes,
)
from api.app.engine.groups import build_candidate_groups


def test_parse_vague_memory_to_clues_heuristics():
    """Verify incomplete memory text is accurately parsed to 1-3 clues."""
    clues = parse_vague_memory_to_clues("I remember being outdoors at night with warm yellow lamps and street food")
    assert len(clues) >= 1
    assert len(clues) <= 3
    cue_ids = [c["cue_id"] for c in clues]
    assert any("lighting" in cid or "setting" in cid or "scene" in cid for cid in cue_ids)


def test_generate_cognitive_cue_cards_non_pictorial():
    """Verify cognitive cue cards are conceptual/sensory cues, not photo thumbnails."""
    cards = generate_cognitive_cue_cards(["lighting_warm_yellow"])
    assert len(cards) == 4
    for card in cards:
        assert "id" in card
        assert "title" in card
        assert "category" in card
        assert "description" in card
        assert "options" in card
        assert len(card["options"]) >= 3
        # Ensure no thumbnail photo URLs are leaked into non-pictorial cognitive cards
        assert "preview_photo_ids" not in card
        assert "thumb_256" not in card


def test_generate_followup_memory_probes_preserves_context():
    """Verify follow-up memory probes retain existing clues without losing context."""
    active_clues = [
        {"cue_id": "setting_outdoors", "label": "Outdoors"},
        {"cue_id": "lighting_warm_yellow", "label": "Warm yellow light"},
    ]
    probes_data = generate_followup_memory_probes(active_clues, macro_albums_count=4)
    assert "preserved_context" in probes_data
    assert "probes" in probes_data
    assert len(probes_data["probes"]) >= 3
    for p in probes_data["probes"]:
        assert "question" in p
        assert len(p["options"]) >= 3


def test_start_session_with_incomplete_memory_query():
    """Verify session starts with parsed initial clues and cognitive cards."""
    client = TestClient(app)
    resp = client.post("/api/session", json={
        "entry": "search_pill",
        "initial_query": "outdoor sunset party with friends",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "cognitive_cards" in data
    assert len(data["cognitive_cards"]) == 4
    assert len(data["initial_clues"]) >= 1


def test_add_memory_text_endpoint():
    """Verify user can type an additional memory fragment at any point."""
    client = TestClient(app)
    start_resp = client.post("/api/session", json={"entry": "search_pill"})
    session_id = start_resp.json()["session_id"]

    add_resp = client.post(f"/api/session/{session_id}/add-memory-text", json={
        "text": "late night gathering with music",
    })
    assert add_resp.status_code == 200
    data = add_resp.json()
    assert data["step"] == "groups"
    assert len(data["clues"]) >= 1
    assert "groups" in data
    assert len(data["groups"]) <= 4
    for g in data["groups"]:
        assert "confidence" in g
        assert "percentage" in g["confidence"]
        assert 0 <= g["confidence"]["percentage"] <= 100


def test_fallback_endpoint_preserves_context_and_probes():
    """Verify not-here/fallback returns retained clues, Groq AI probes, and zero context loss."""
    client = TestClient(app)
    start_resp = client.post("/api/session", json={"entry": "search_pill", "initial_query": "outdoor tea stall"})
    session_id = start_resp.json()["session_id"]

    fallback_resp = client.post(f"/api/session/{session_id}/fallback")
    assert fallback_resp.status_code == 200
    data = fallback_resp.json()
    assert data["step"] == "fallback"
    assert "clues" in data
    assert len(data["clues"]) >= 1  # Context NOT lost!
    assert "followup_probes" in data
    assert len(data["followup_probes"]) >= 3
    assert "preserved_context" in data


def test_four_macro_albums_with_confidence_percentages():
    """Verify groups are structured as up to 4 macro albums with confidence percentages."""
    client = TestClient(app)
    start_resp = client.post("/api/session", json={"entry": "search_pill"})
    session_id = start_resp.json()["session_id"]

    select_resp = client.post(f"/api/session/{session_id}/cues", json={
        "cue_ids": ["setting_outdoors", "lighting_bright_daylight"]
    })
    assert select_resp.status_code == 200
    data = select_resp.json()
    groups = data.get("groups", [])
    assert len(groups) <= 4
    for g in groups:
        assert "confidence" in g
        conf = g["confidence"]
        assert "percentage" in conf
        assert "percentage_label" in conf
        assert isinstance(conf["percentage"], int)
