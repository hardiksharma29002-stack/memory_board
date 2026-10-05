"""Groq-powered cognitive memory assistant for vague photo retrieval.

Uses fast Groq LLM inference (qwen/qwen3.8-27b) with robust local fallbacks.
Enables users to type or select clues, generates conceptual non-pictorial memory cards,
and synthesizes context-preserving follow-up probes when searching.
"""

import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import requests

from ..vocab import CUE_LOOKUP, CUES

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "qwen/qwen3.8-27b"


_GROQ_CACHE: Dict[str, str] = {}


def call_groq_chat(prompt: str, system_prompt: str = "", max_tokens: int = 350) -> Optional[str]:
    """Call Groq API with in-memory caching, fast timeout, and fallback to respect rate limits."""
    cache_key = f"{prompt}:{system_prompt}:{max_tokens}"
    if cache_key in _GROQ_CACHE:
        return _GROQ_CACHE[cache_key]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            GROQ_URL,
            headers=headers,
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=4.5,
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if content:
                # Keep cache bounded to 150 entries
                if len(_GROQ_CACHE) > 150:
                    _GROQ_CACHE.pop(next(iter(_GROQ_CACHE)))
                _GROQ_CACHE[cache_key] = content
            return content
        else:
            return None
    except Exception:
        return None


def parse_vague_memory_to_clues(user_text: str) -> List[Dict[str, str]]:
    """Parse user's incomplete memory input into 1-3 structured clues."""
    if not user_text or not user_text.strip():
        return []

    # Fast rule-based check first
    matched_clues = []
    text_lower = user_text.lower()

    # Canonical cue alias dictionary for cognitive mapping
    cue_aliases = {
        "people_just_me": "people_solo",
        "people_1_person": "people_solo",
        "people_single": "people_solo",
        "people_2_people": "people_pair",
        "people_couple": "people_pair",
        "people_3_5_people": "people_group",
        "people_friends": "people_group",
        "people_family": "people_group",
        "people_big_crowd": "people_crowd",
        "cafe": "setting_food_place",
        "restaurant": "setting_food_place",
        "dhaba": "setting_food_place",
        "food": "setting_food_place",
        "beach": "scene_water_beach",
        "river": "scene_water_beach",
        "lake": "scene_water_beach",
        "park": "scene_greenery_park",
        "garden": "scene_greenery_park",
        "home": "setting_home",
        "vehicle": "setting_vehicle",
        "car": "setting_vehicle",
        "monument": "scene_buildings",
        "temple": "scene_temple_festival",
        "mandir": "scene_temple_festival",
        "puja": "scene_celebration",
        "pooja": "scene_celebration",
        "celebration": "scene_celebration",
        "aarti": "scene_celebration",
        "festival": "scene_temple_festival",
    }

    # Rule-based dictionary for immediate latency-free matching
    rules = [
        (r"night|dark|evening|dinner|late", "lighting_night_dark", "Night or dark setting"),
        (r"morning|daylight|sun|afternoon|bright", "lighting_bright_daylight", "Bright daylight"),
        (r"yellow|warm|lamp|candle|golden|sunset", "lighting_warm_yellow", "Warm yellow light"),
        (r"neon|colorful|party|club|disco", "lighting_neon_lights", "Neon or colorful lights"),
        (r"outdoors|street|outside|park|garden|road", "setting_outdoors", "Outdoors"),
        (r"indoors|inside|room|office|hall", "setting_indoors", "Indoors"),
        (r"food|cafe|restaurant|chai|tea|eating|meal|snack|stall|dining", "setting_food_place", "Cafe / restaurant"),
        (r"puja|pooja|aarti|prasad|havan|archana|garba|ritual", "scene_celebration", "Puja & Rituals"),
        (r"temple|mandir", "scene_buildings", "Temple / Heritage"),
        (r"wedding|party|birthday|anniversary|celebration|event", "scene_celebration", "Celebrations & Events"),
        (r"diyas|diwali|rangoli|holi|festive", "scene_temple_festival", "Festive Celebrations"),
        (r"beach|sea|water|river|lake|pool", "scene_water_beach", "Water or beach"),
        (r"alone|solo|myself|selfie|just me", "people_solo", "Just me / 1 person"),
        (r"two of us|couple|friend and me|2 people", "people_pair", "2 people"),
        (r"group|friends|family|3 people|4 people|few of us", "people_group", "3 to 5 people"),
        (r"crowd|lots of people|packed|audience", "people_crowd", "Big crowd"),
    ]

    for pattern, cue_id, label in rules:
        if re.search(pattern, text_lower):
            cid = cue_aliases.get(cue_id, cue_id)
            lbl = CUE_LOOKUP[cid].label if cid in CUE_LOOKUP else label
            matched_clues.append({
                "cue_id": cid,
                "label": lbl,
                "source": "memory_text",
            })
            if len(matched_clues) >= 3:
                break

    # If we got at least 1-2 clues from rules, return them immediately
    if len(matched_clues) >= 2:
        return matched_clues[:3]

    # Otherwise enhance with Groq LLM
    system_prompt = (
        "You are an assistant for Google Photos Memory Board. The user describes a vague photo memory. "
        "Extract up to 3 cognitive memory clues (time/lighting, setting/place, people count, event). "
        "Return valid JSON array of objects with keys 'cue_id', 'label'. "
        "Allowed cue_ids include: lighting_warm_yellow, lighting_bright_daylight, lighting_night_dark, "
        "lighting_neon_lights, setting_indoors, setting_outdoors, setting_food_place, scene_celebration, "
        "scene_water_beach, scene_greenery_park, people_solo, people_pair, people_group, people_crowd."
    )
    llm_resp = call_groq_chat(f"Memory: '{user_text}'", system_prompt=system_prompt, max_tokens=150)
    if llm_resp:
        try:
            # Clean markdown codeblocks if any
            clean_json = re.sub(r"```json|```", "", llm_resp).strip()
            parsed = json.loads(clean_json)
            if isinstance(parsed, list) and len(parsed) > 0:
                results = []
                for item in parsed[:3]:
                    raw_cid = item.get("cue_id", "")
                    cid = cue_aliases.get(raw_cid, raw_cid)
                    if cid in CUE_LOOKUP:
                        results.append({
                            "cue_id": cid,
                            "label": CUE_LOOKUP[cid].label,
                            "source": "groq_ai",
                        })
                    else:
                        results.append({
                            "cue_id": cid or "setting_indoors",
                            "label": item.get("label", user_text[:30]),
                            "source": "groq_ai",
                        })
                if results:
                    return results
        except Exception:
            pass

    return matched_clues if matched_clues else [{"cue_id": "setting_outdoors", "label": "Outdoors", "source": "fallback"}]


def generate_cognitive_cue_cards(selected_clues: List[str]) -> List[Dict[str, Any]]:
    """Generate conceptual, non-pictorial memory cards that stimulate user episodic recall.

    These cards are NOT pictorial photo strips. Instead they are rich story & sensory cues:
    - Sensory & Lighting Atmosphere
    - Social Dynamics & Group Energy
    - Setting & Background Texture
    - Occasion / Emotional Tone
    """
    cards = [
        {
            "id": "card_sensory_lighting",
            "title": "Lighting & Atmosphere",
            "category": "Sensory Cue",
            "description": "How did the light feel in that exact moment?",
            "options": [
                {"id": "lighting_warm_yellow", "label": "Warm golden lamps & evening yellow", "icon": "sunset"},
                {"id": "lighting_bright_daylight", "label": "Crisp outdoor natural daylight", "icon": "sun"},
                {"id": "lighting_night_dark", "label": "Dark night with focal illumination", "icon": "moon"},
                {"id": "lighting_neon_lights", "label": "Vibrant colorful or neon festive lighting", "icon": "sparkles"},
            ],
        },
        {
            "id": "card_social_dynamics",
            "title": "People & Presence",
            "category": "Social Cue",
            "description": "Who was standing or sitting in the frame?",
            "options": [
                {"id": "people_just_me", "label": "Solo shot or personal perspective", "icon": "user"},
                {"id": "people_2_people", "label": "Two people sharing the moment", "icon": "users"},
                {"id": "people_3_5_people", "label": "Close circle or group of 3 to 5", "icon": "users"},
                {"id": "people_big_crowd", "label": "Surrounded by a bustling crowd", "icon": "crowd"},
            ],
        },
        {
            "id": "card_setting_action",
            "title": "Place & Surroundings",
            "category": "Spatial Cue",
            "description": "What was the backdrop or immediate venue?",
            "options": [
                {"id": "setting_food_place", "label": "Food stall, restaurant, or cafe table", "icon": "coffee"},
                {"id": "setting_outdoors", "label": "Open-air street, park, or tourist sight", "icon": "compass"},
                {"id": "setting_indoors", "label": "Cozy home room, hall, or workspace", "icon": "home"},
                {"id": "scene_celebration", "label": "Celebration, party, or special event", "icon": "gift"},
            ],
        },
        {
            "id": "card_color_mood",
            "title": "Dominant Color & Mood",
            "category": "Visual Tone",
            "description": "What color or vibe stands out in your recollection?",
            "options": [
                {"id": "color_warm", "label": "Rich warm, golden, or vibrant colors", "icon": "palette"},
                {"id": "color_cool", "label": "Deep blues, sky, water, or lush greenery", "icon": "droplet"},
                {"id": "scene_water_beach", "label": "Riverside, ghat, beach, or rain glistening", "icon": "waves"},
                {"id": "scene_greenery_park", "label": "Lush trees, gardens, or natural scenery", "icon": "trees"},
            ],
        },
    ]

    return cards


def generate_smart_cognitive_cards(query: str = "", selected_clues: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Generate dynamic, intelligent memory cue cards using Groq AI tailored to the user's clues."""
    selected_clues = selected_clues or []
    base_cards = generate_cognitive_cue_cards(selected_clues)

    if not query and not selected_clues:
        return base_cards

    clues_text = ", ".join(selected_clues)
    prompt = f"User photo memory context: Query='{query}', Cues='{clues_text}'. Generate 4 cognitive memory cards."
    system_prompt = (
        "You are an expert cognitive memory assistant for photo retrieval. "
        "Generate 4 non-pictorial cognitive cards that trigger episodic human memory. "
        "Each card must have: "
        "'id' (string), 'title' (string), 'category' (string), 'description' (string), "
        "and 'options' (array of 4 objects each with 'id', 'label', 'icon'). "
        "Icons can be: sun, sunset, moon, sparkles, user, users, crowd, coffee, compass, home, gift, palette, droplet, waves, trees. "
        "Return valid JSON array of 4 card objects."
    )

    llm_resp = call_groq_chat(prompt, system_prompt=system_prompt, max_tokens=400)
    if llm_resp:
        try:
            clean_json = re.sub(r"```json|```", "", llm_resp).strip()
            parsed = json.loads(clean_json)
            if isinstance(parsed, list) and len(parsed) >= 2:
                valid_cards = []
                for c in parsed[:4]:
                    if "id" in c and "title" in c and "options" in c and isinstance(c["options"], list):
                        valid_cards.append({
                            "id": str(c["id"]),
                            "title": str(c["title"]),
                            "category": str(c.get("category", "Memory Cue")),
                            "description": str(c.get("description", "What do you recall?")),
                            "options": [
                                {
                                    "id": str(opt.get("id", f"{c['id']}_{i}")),
                                    "label": str(opt.get("label", "Option")),
                                    "icon": str(opt.get("icon", "sparkles")),
                                }
                                for i, opt in enumerate(c["options"][:4])
                            ],
                        })
                if len(valid_cards) >= 2:
                    return valid_cards
        except Exception:
            pass

    return base_cards


def generate_followup_memory_probes(
    active_clues: List[Dict[str, Any]],
    macro_albums_count: int = 4,
) -> Dict[str, Any]:
    """Generate contextual follow-up probes when user needs more clues without losing context."""
    clue_labels = [c.get("label", c.get("value", "")) for c in active_clues]
    clues_str = ", ".join(clue_labels) if clue_labels else "your previous clues"

    system_prompt = (
        "You are an empathetic memory retrieval assistant in Google Photos. "
        "The user hasn't found their photo yet in the 4 albums. "
        "Based on their existing locked clues, suggest 3 distinct, highly memorable sensory questions "
        "that help them trigger forgotten memory anchors without losing their current context. "
        "Return JSON with 'summary' and 'probes': [{'question': '...', 'options': ['opt1', 'opt2', 'opt3', 'opt4']}]."
    )

    llm_resp = call_groq_chat(
        f"Active clues kept: {clues_str}. Give 3 fresh memory probes.",
        system_prompt=system_prompt,
        max_tokens=250,
    )

    if llm_resp:
        try:
            clean_json = re.sub(r"```json|```", "", llm_resp).strip()
            data = json.loads(clean_json)
            if "probes" in data:
                return {
                    "preserved_context": clue_labels,
                    "message": f"Kept all {len(clue_labels)} clues in mind. Let's trigger a fresh memory angle:",
                    "probes": data["probes"][:3],
                }
        except Exception:
            pass

    # Built-in fallback probes preserving context
    return {
        "preserved_context": clue_labels,
        "message": f"Kept all {len(clue_labels)} clues in mind. Let's trigger a fresh memory angle:",
        "probes": [
            {
                "question": "What was the camera or shot style?",
                "options": ["Close-up candid portrait", "Wide landscape / venue view", "Quick snapshot / WhatsApp forward", "Posed group photo"],
            },
            {
                "question": "Was there any distinct object in view?",
                "options": ["Plates of food / chai glasses", "Festive decorations / diyas / flowers", "Vehicle / rickshaw / car", "Signs, stage, or posters"],
            },
            {
                "question": "Was it taken on a special trip or everyday routine?",
                "options": ["Out-of-town trip / vacation", "Festive / wedding celebration", "College / work hangout", "Just an ordinary day"],
            },
        ],
    }
