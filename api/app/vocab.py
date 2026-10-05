"""Vocabulary and prompt definitions for Memory Board.

Defines the ~40 memory cues across 5 cognitive groups (Appendix A),
the information-gain question bank (Appendix B),
and the 'Almost!' pivot options (Appendix C).
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Cue:
    id: str
    group: str           # lighting, setting, scene, people, color
    label: str           # Human-readable short label
    prompt: str          # Text prompt for CLIP zero-shot matching
    is_rule_based: bool = False  # E.g. people count is derived from face_count


# ─── Appendix A: Cue Vocabulary ───────────────────────────────────────────────

CUES: List[Cue] = [
    # 💡 Lighting (6 cues)
    Cue("lighting_warm_yellow", "lighting", "Warm yellow light", "warm yellow ambient light evening indoor lighting"),
    Cue("lighting_bright_daylight", "lighting", "Bright daylight", "bright sunny outdoor daylight sunshine clear sky"),
    Cue("lighting_golden_hour", "lighting", "Golden hour / sunset", "golden hour sunset sunrise warm orange sunlight"),
    Cue("lighting_night_dark", "lighting", "Night / dark", "night time dark dimly lit darkness city lights"),
    Cue("lighting_neon_lights", "lighting", "Neon / party lights", "colorful neon lights party club stage lighting"),
    Cue("lighting_flash", "lighting", "Flash photo", "direct camera flash bright front lighting dark background"),

    # 📍 Setting (7 cues)
    Cue("setting_indoors", "setting", "Indoors", "indoors inside a room room interior walls ceiling"),
    Cue("setting_outdoors", "setting", "Outdoors", "outdoors in nature open sky exterior outside"),
    Cue("setting_vehicle", "setting", "In a vehicle", "inside vehicle car auto rickshaw bus train window"),
    Cue("setting_home", "setting", "At home", "at home living room balcony bedroom kitchen cozy house"),
    Cue("setting_food_place", "setting", "Cafe / restaurant", "cafe coffee shop restaurant dhaba eatery dining table"),
    Cue("setting_event_venue", "setting", "College / hall / venue", "college campus auditorium wedding hall event venue"),
    Cue("setting_street", "setting", "Street / market", "street road market bazaar vendor sidewalk traffic"),

    # 🏞️ Scene (10 cues)
    Cue("scene_food_stall", "scene", "Food & chai", "street food stall chai tea cup thali meal eating"),
    Cue("scene_stage", "scene", "Stage / performance", "stage performance auditorium dance presentation fest"),
    Cue("scene_water_beach", "scene", "Water / beach / river", "beach sea ocean river water ghat lake shoreline"),
    Cue("scene_greenery_park", "scene", "Greenery / park", "green park garden trees plants grass nature lawn"),
    Cue("scene_rooftop", "scene", "Rooftop / terrace", "rooftop terrace balcony city view open sky parapet"),
    Cue("scene_crowd", "scene", "Crowd / gathering", "crowd of people gathering audience group celebration"),
    Cue("scene_celebration", "scene", "Celebration / puja", "celebration party birthday cake garlands festival puja ritual"),
    Cue("scene_buildings", "scene", "Buildings / monuments", "city buildings architecture monument temple fort towers"),
    Cue("scene_mountains", "scene", "Hills / mountains", "mountains hills valley mountain road nature landscape"),
    Cue("scene_temple_festival", "scene", "Festival / rangoli / diyas", "diwali diyas rangoli holi colors festive temple decoration"),

    # 👥 People (4 rule-based cues from face_count)
    Cue("people_solo", "people", "Just me / 1 person", "portrait single person one person alone", is_rule_based=True),
    Cue("people_pair", "people", "2 people", "two people couple friends selfie duo", is_rule_based=True),
    Cue("people_group", "people", "3 to 5 people", "group of friends family three to five people", is_rule_based=True),
    Cue("people_crowd", "people", "Big crowd", "large crowd many people group photo crowd", is_rule_based=True),

    # 🎨 Colour Mood (5 cues)
    Cue("color_warm", "color", "Warm (yellow/orange)", "warm yellow orange golden tones cozy atmosphere"),
    Cue("color_cool", "color", "Cool (blue/green)", "cool blue green turquoise teal outdoor tone"),
    Cue("color_dark", "color", "Dark / moody", "dark shadows low key moody black dark atmosphere"),
    Cue("color_bright", "color", "Bright / white", "bright clean high key white light airy fresh"),
    Cue("color_red", "color", "Festive red / vibrant", "vibrant red maroon deep warm festive celebration colors"),
]

CUE_LOOKUP: Dict[str, Cue] = {c.id: c for c in CUES}
CUES_BY_GROUP: Dict[str, List[Cue]] = {}
for c in CUES:
    CUES_BY_GROUP.setdefault(c.group, []).append(c)


# ─── Appendix B: Question Bank ────────────────────────────────────────────────

@dataclass
class QuestionOption:
    id: str
    label: str
    cue_id: Optional[str]  # Associated cue ID if applicable


@dataclass
class Question:
    id: str
    prompt: str
    options: List[QuestionOption]


QUESTIONS: List[Question] = [
    Question(
        id="q_time",
        prompt="What time of day was it?",
        options=[
            QuestionOption("opt_morning", "Morning", "lighting_bright_daylight"),
            QuestionOption("opt_afternoon", "Afternoon", "lighting_bright_daylight"),
            QuestionOption("opt_evening", "Evening", "lighting_golden_hour"),
            QuestionOption("opt_night", "Night", "lighting_night_dark"),
        ],
    ),
    Question(
        id="q_place",
        prompt="Where was it?",
        options=[
            QuestionOption("opt_home", "Home", "setting_home"),
            QuestionOption("opt_food", "Food place / cafe", "setting_food_place"),
            QuestionOption("opt_outdoors", "Outdoors / trip", "setting_outdoors"),
            QuestionOption("opt_venue", "College / event venue", "setting_event_venue"),
        ],
    ),
    Question(
        id="q_people",
        prompt="How many people were in it?",
        options=[
            QuestionOption("opt_solo", "Just me", "people_solo"),
            QuestionOption("opt_pair", "2 people", "people_pair"),
            QuestionOption("opt_group", "3 to 5", "people_group"),
            QuestionOption("opt_crowd", "Big crowd", "people_crowd"),
        ],
    ),
    Question(
        id="q_background",
        prompt="What was in the background?",
        options=[
            QuestionOption("opt_water", "Water or sky", "scene_water_beach"),
            QuestionOption("opt_buildings", "Buildings or street", "scene_buildings"),
            QuestionOption("opt_greenery", "Greenery or park", "scene_greenery_park"),
            QuestionOption("opt_room", "A room or walls", "setting_indoors"),
        ],
    ),
    Question(
        id="q_colour",
        prompt="What colour stood out?",
        options=[
            QuestionOption("opt_warm", "Warm yellow/orange", "color_warm"),
            QuestionOption("opt_cool", "Cool blue/green", "color_cool"),
            QuestionOption("opt_dark", "Dark", "color_dark"),
            QuestionOption("opt_bright", "Bright white", "color_bright"),
        ],
    ),
    Question(
        id="q_source",
        prompt="How did it reach you?",
        options=[
            QuestionOption("opt_camera", "I took it", None),
            QuestionOption("opt_received", "Someone sent it", None),
            QuestionOption("opt_screenshot", "Screenshot", None),
            QuestionOption("opt_saved", "Saved from somewhere", None),
        ],
    ),
    Question(
        id="q_occasion",
        prompt="What was the occasion?",
        options=[
            QuestionOption("opt_trip", "Trip / travel", "scene_mountains"),
            QuestionOption("opt_celebration", "Celebration / party", "scene_celebration"),
            QuestionOption("opt_college_work", "College or work", "setting_event_venue"),
            QuestionOption("opt_everyday", "Everyday life", "setting_home"),
        ],
    ),
]

QUESTION_LOOKUP: Dict[str, Question] = {q.id: q for q in QUESTIONS}


# ─── Appendix C: Almost! Options ──────────────────────────────────────────────

ALMOST_OPTIONS = [
    {"id": "diff_place", "label": "Different place", "axis": "setting"},
    {"id": "diff_time", "label": "Different time of day", "axis": "lighting"},
    {"id": "diff_people", "label": "Different people", "axis": "people"},
    {"id": "diff_look", "label": "Different look (clothes or colours)", "axis": "color"},
    {"id": "cant_say", "label": "Can't say / not sure", "axis": "none"},
]
