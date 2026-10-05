#!/usr/bin/env python3
"""Automated demo script simulating a full cognitive memory search session."""

import sys
import requests

BASE_URL = "http://localhost:8000"


def run_demo():
    print("=" * 60)
    print("🧠 Memory Board Cognitive Retrieval Walk-through")
    print("=" * 60)

    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health")
    if res.status_code != 200:
        print("❌ Backend is not running on http://localhost:8000")
        return
    data = res.json()
    print(f"✅ Backend healthy: {data['photos_indexed']} photos indexed.")

    # 2. Start session with vague memory
    query = "sunset with tea and warm vibes"
    print(f"\n🔍 Starting search session for memory: '{query}'")
    s_res = requests.post(f"{BASE_URL}/api/session", json={"entry": "search_pill", "initial_query": query})
    session = s_res.json()
    sid = session["session_id"]
    print(f"✅ Session initialized: {sid}")
    print(f"📋 Initial clues extracted: {[c['label'] for c in session.get('initial_clues', [])]}")

    # 3. Simulate answering a guided question
    q_res = requests.post(f"{BASE_URL}/api/session/{sid}/none")
    q_data = q_res.json()
    question = q_data.get("question")
    if question:
        print(f"\n❓ Guided Recall Question: {question['prompt']}")
        options = [opt['label'] for opt in question['options']]
        print(f"👉 Options: {options}")

    print("\n🎉 Walk-through completed successfully!")


if __name__ == "__main__":
    run_demo()
