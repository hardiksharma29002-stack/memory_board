"""Cue Board generator implementing memory-triggering cards based on user clues and MMR diversity."""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from sqlmodel import Session, select

from ..config import CONFIG
from ..database import engine
from ..models import Photo, PhotoTag
from ..vocab import CUES, CUE_LOOKUP, Cue


# Memory Trigger Metadata mapping for each cue
CUE_METADATA: Dict[str, dict] = {
    # 💡 Lighting & Atmosphere
    "lighting_warm_yellow": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#golden-glow", "#evening-lights", "#ambient", "#cozy-lights"],
        "hint": "Warm ambient lighting or indoor evening glow",
    },
    "lighting_bright_daylight": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#sunshine", "#clear-sky", "#outdoors", "#daytime"],
        "hint": "Bright sunny daylight or open morning sun",
    },
    "lighting_golden_hour": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#sunset", "#golden-hour", "#warm-horizon", "#dusk"],
        "hint": "Sunset or golden hour warm sunlight",
    },
    "lighting_night_dark": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#nighttime", "#dimly-lit", "#dark-backdrop", "#city-lights"],
        "hint": "Dark nighttime backdrop or night illumination",
    },
    "lighting_neon_lights": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#colorful-lights", "#stage-lights", "#neon", "#celebration"],
        "hint": "Colorful party or stage illumination",
    },
    "lighting_flash": {
        "dimension": "Lighting & Atmosphere",
        "tags": ["#camera-flash", "#front-lit", "#party-snap"],
        "hint": "Crisp direct flash lighting",
    },

    # 📍 Background & Setting / Scene
    "setting_street": {
        "dimension": "Background & Setting",
        "tags": ["#bazaar", "#roadside", "#city-buzz", "#market"],
        "hint": "Outdoor street market, bazaar or traffic",
    },
    "setting_indoors": {
        "dimension": "Background & Setting",
        "tags": ["#inside-room", "#living-area", "#restaurant", "#cozy-interior"],
        "hint": "Indoor room, hall or interior space",
    },
    "setting_outdoors": {
        "dimension": "Background & Setting",
        "tags": ["#open-air", "#courtyard", "#nature", "#skyline"],
        "hint": "Outdoors in nature or open exterior",
    },
    "setting_food_place": {
        "dimension": "Background & Setting",
        "tags": ["#cafe", "#dhaba", "#dining-table", "#restaurant"],
        "hint": "Cafe, eatery or dining table",
    },
    "setting_event_venue": {
        "dimension": "Background & Setting",
        "tags": ["#college-fest", "#auditorium", "#hall", "#banquet"],
        "hint": "Auditorium, college fest or event hall",
    },
    "scene_food_stall": {
        "dimension": "Background & Setting",
        "tags": ["#chai-tea", "#street-food", "#dining", "#snack"],
        "hint": "Tea stall, street food or thali meals",
    },
    "scene_celebration": {
        "dimension": "Background & Setting",
        "tags": ["#festival", "#puja", "#party", "#birthday", "#decor"],
        "hint": "Celebration, birthday party or ceremony",
    },
    "scene_temple_festival": {
        "dimension": "Background & Setting",
        "tags": ["#diyas", "#rangoli", "#temple", "#tradition", "#festive-vibes"],
        "hint": "Festive decorations, rangoli or diyas",
    },
    "scene_water_beach": {
        "dimension": "Background & Setting",
        "tags": ["#waterfront", "#river-ghat", "#beach", "#shoreline"],
        "hint": "Waterfront, river ghat or lake",
    },
    "scene_greenery_park": {
        "dimension": "Background & Setting",
        "tags": ["#green-trees", "#garden", "#plants", "#nature-walk"],
        "hint": "Green garden, trees or lawn",
    },
    "scene_mountains": {
        "dimension": "Background & Setting",
        "tags": ["#hills", "#mountain-view", "#scenic", "#travel"],
        "hint": "Hills, mountains or valley landscape",
    },
    "scene_buildings": {
        "dimension": "Background & Setting",
        "tags": ["#architecture", "#monument", "#heritage", "#fort"],
        "hint": "Historic buildings or monuments",
    },

    # 🎨 Sense & Color Palette
    "color_warm": {
        "dimension": "Sense & Color Palette",
        "tags": ["#yellow-tones", "#marigold", "#amber", "#saffron"],
        "hint": "Warm yellow and orange dominant palette",
    },
    "color_red": {
        "dimension": "Sense & Color Palette",
        "tags": ["#vibrant-red", "#festive-maroon", "#rich-palette"],
        "hint": "Rich red and festive warm shades",
    },
    "color_cool": {
        "dimension": "Sense & Color Palette",
        "tags": ["#blue-sky", "#teal", "#greenery", "#cool-breeze"],
        "hint": "Cool blue, turquoise and leafy green tones",
    },
    "color_bright": {
        "dimension": "Sense & Color Palette",
        "tags": ["#bright-white", "#airy", "#crisp-contrast"],
        "hint": "High-key bright daylight and clean colors",
    },
    "color_dark": {
        "dimension": "Sense & Color Palette",
        "tags": ["#moody-tones", "#shadows", "#deep-contrast"],
        "hint": "Moody deep contrast and dark shades",
    },

    # 👥 People & Social Dynamic
    "people_solo": {
        "dimension": "People & Dynamic",
        "tags": ["#single-person", "#portrait", "#solo-moment"],
        "hint": "Focus on 1 person in the frame",
    },
    "people_pair": {
        "dimension": "People & Dynamic",
        "tags": ["#duo", "#two-people", "#friends", "#couple"],
        "hint": "2 people together or a selfie duo",
    },
    "people_group": {
        "dimension": "People & Dynamic",
        "tags": ["#group-of-friends", "#family", "#3-5-people", "#laughter"],
        "hint": "Small group of 3 to 5 people",
    },
    "people_crowd": {
        "dimension": "People & Dynamic",
        "tags": ["#crowd", "#gathering", "#festive-rush", "#public-event"],
        "hint": "Large crowd or bustling gathering",
    },
}


@dataclass
class CueCard:
    cue_id: str
    label: str
    group: str
    dimension: str
    tags: List[str]
    hint: str
    photo_count: int
    preview_photo_ids: List[str]
    palette: List[str]


def compute_cue_support(db: Session, score_threshold: float = 0.20) -> Dict[str, Set[str]]:
    """Compute which photos match each cue."""
    tags = db.exec(
        select(PhotoTag.cue_id, PhotoTag.photo_id)
        .where(PhotoTag.score >= score_threshold)
    ).all()

    cue_matches: Dict[str, Set[str]] = {}
    for cue_id, photo_id in tags:
        cue_matches.setdefault(cue_id, set()).add(photo_id)

    return cue_matches


def jaccard_overlap(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def score_cue_relevance_to_query(cue_id: str, query: str) -> float:
    """Score how relevant a cue is to a user's text clues/query."""
    if not query:
        return 1.0

    tokens = [w.lower() for w in re.findall(r"\w+", query)]
    if not tokens:
        return 1.0

    cue_def = CUE_LOOKUP.get(cue_id)
    meta = CUE_METADATA.get(cue_id, {})
    tags = [t.replace("#", "").lower() for t in meta.get("tags", [])]
    label_tokens = [w.lower() for w in re.findall(r"\w+", cue_def.label if cue_def else "")]
    prompt_tokens = [w.lower() for w in re.findall(r"\w+", cue_def.prompt if cue_def else "")]
    dim_tokens = [w.lower() for w in re.findall(r"\w+", meta.get("dimension", ""))]

    score = 0.0
    for tok in tokens:
        if tok in label_tokens:
            score += 3.0
        if tok in tags:
            score += 2.5
        if tok in prompt_tokens:
            score += 1.5
        if tok in dim_tokens:
            score += 1.0

        # Substring / partial matches (e.g. "light" in "lighting")
        for lt in label_tokens:
            if tok in lt or lt in tok:
                score += 1.2
        for tag in tags:
            if tok in tag or tag in tok:
                score += 1.0

    return score


def generate_cue_cards(query: Optional[str] = None, target_engine=None) -> List[CueCard]:
    """Generate 3-4 diverse memory-triggering cards tailored to user clues/query."""
    eng = target_engine or engine

    with Session(eng) as db:
        all_photos = db.exec(select(Photo)).all()
        total_photos = len(all_photos)
        if total_photos == 0:
            return []

        photo_lookup = {p.id: p for p in all_photos}
        cue_matches = compute_cue_support(db)

        # Target 4 perceptual memory dimensions
        DIMENSIONS = [
            ("Lighting & Atmosphere", ["lighting_warm_yellow", "lighting_bright_daylight", "lighting_golden_hour", "lighting_night_dark", "lighting_neon_lights"]),
            ("Background & Setting", ["setting_street", "setting_indoors", "setting_outdoors", "scene_food_stall", "scene_celebration", "scene_temple_festival", "scene_water_beach"]),
            ("Sense & Color Palette", ["color_warm", "color_red", "color_cool", "color_bright", "color_dark"]),
            ("People & Dynamic", ["people_group", "people_crowd", "people_pair", "people_solo"]),
        ]

        selected_cues: List[str] = []

        for dim_name, eligible_cues in DIMENSIONS:
            # Score each candidate cue in this dimension
            scored_cues = []
            for cid in eligible_cues:
                photos_set = cue_matches.get(cid, set())
                photo_count = len(photos_set)
                if photo_count == 0:
                    continue

                rel_score = score_cue_relevance_to_query(cid, query) if query else 1.0
                support = photo_count / total_photos
                balance_score = 1.0 - abs(support - 0.35)

                final_score = rel_score * 2.0 + balance_score
                scored_cues.append((cid, final_score, photos_set))

            if scored_cues:
                scored_cues.sort(key=lambda x: x[1], reverse=True)
                selected_cues.append(scored_cues[0][0])

        # If less than 4, fill from remaining top cues
        if len(selected_cues) < 3:
            for cid in cue_matches.keys():
                if cid not in selected_cues and cid in CUE_LOOKUP:
                    selected_cues.append(cid)
                    if len(selected_cues) >= 4:
                        break

        # Limit to 3 or 4 cards per spec
        selected_cues = selected_cues[:4]

        # Build CueCard objects
        cards: List[CueCard] = []
        for cid in selected_cues:
            cue_def = CUE_LOOKUP.get(cid, Cue(cid, "other", cid, ""))
            meta = CUE_METADATA.get(cid, {
                "dimension": "Perceptual Memory",
                "tags": [f"#{cid.replace('_', '-')}"],
                "hint": "Recall this visual facet",
            })

            p_set = cue_matches.get(cid, set())
            sorted_photos = sorted(
                [photo_lookup[pid] for pid in p_set if pid in photo_lookup],
                key=lambda p: (p.sharpness, p.brightness),
                reverse=True,
            )

            preview_ids = [p.id for p in sorted_photos[:3]]

            # Sample palette from matching photos
            sample_palette = ["#e28743", "#1e3d59", "#f5f0e1"]
            if sorted_photos:
                try:
                    loaded = json.loads(sorted_photos[0].palette)
                    if len(loaded) >= 3:
                        sample_palette = loaded[:3]
                except Exception:
                    pass

            cards.append(CueCard(
                cue_id=cid,
                label=cue_def.label,
                group=cue_def.group,
                dimension=meta.get("dimension", "Memory Facet"),
                tags=meta.get("tags", []),
                hint=meta.get("hint", ""),
                photo_count=len(p_set),
                preview_photo_ids=preview_ids,
                palette=sample_palette,
            ))

        return cards
