"""Candidate photo grouping and cluster ranking."""

from dataclasses import dataclass
import os
import re
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from sklearn.cluster import KMeans
from sqlmodel import Session, select

from ..config import CONFIG, EMBEDDINGS_PATH
from ..database import engine
from ..models import Photo, PhotoTag, PhotoActivity
from ..vocab import CUE_LOOKUP, CUES
from .confidence import compute_confidence, apply_tie_breaking, ConfidenceScore


@dataclass
class GroupResult:
    id: str
    label: str
    confidence: dict
    why_chips: List[str]
    photos: List[dict]


CUE_FRIENDLY_NAMES: Dict[str, str] = {
    "lighting_warm_yellow": "Warm Golden Glow",
    "lighting_bright_daylight": "Bright Daylight",
    "lighting_golden_hour": "Golden Hour Sunset",
    "lighting_night_dark": "Night Lights",
    "lighting_neon_lights": "Neon & Night Vibes",
    "lighting_flash": "Flash Candids",
    "setting_indoors": "Cozy Indoors",
    "setting_outdoors": "Outdoor Gathering",
    "setting_vehicle": "On the Road",
    "setting_home": "Home Moments",
    "setting_food_place": "Cafe & Dining",
    "setting_event_venue": "Event Hall & Stage",
    "setting_street": "Street & City Walk",
    "scene_food_stall": "Food & Refreshments",
    "scene_stage": "Stage & Performances",
    "scene_water_beach": "Beach & Waterside",
    "scene_greenery_park": "Park & Greenery",
    "scene_rooftop": "Rooftop Views",
    "scene_crowd": "Crowd & Gathering",
    "scene_celebration": "Celebrations & Events",
    "scene_buildings": "Architecture & Monuments",
    "scene_mountains": "Mountain Views",
    "scene_temple_festival": "Festive Celebrations",
    "people_solo": "Solo Portraits",
    "people_pair": "Duo Candids",
    "people_group": "Group Candids",
    "people_crowd": "Lively Crowd",
    "color_warm": "Warm Amber Tones",
    "color_cool": "Cool Blues & Greenery",
    "color_dark": "Moody Shadows",
    "color_bright": "Airy Bright Tones",
    "color_red": "Vibrant Festive Colors",
}


def extract_query_intent(query: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Extract primary topic and vibe from user's text query."""
    if not query or not query.strip():
        return None, None
    q = query.lower().strip()

    if "birthday" in q:
        topic = "Birthday"
    elif "wedding" in q:
        topic = "Wedding"
    elif "puja" in q or "pooja" in q or "aarti" in q:
        topic = "Puja"
    elif "party" in q:
        topic = "Party"
    elif "convocation" in q or "graduation" in q:
        topic = "Graduation"
    elif "diwali" in q or "festival" in q or "holi" in q:
        topic = "Festive"
    elif "trip" in q or "vacation" in q or "tour" in q or "travel" in q or "roadtrip" in q:
        topic = "Trip"
    elif "beach" in q or "sea" in q or "ocean" in q:
        topic = "Beach"
    elif "dinner" in q or "lunch" in q or "food" in q or "cafe" in q or "restaurant" in q:
        topic = "Dining"
    elif "mountain" in q or "hill" in q or "trek" in q or "hike" in q:
        topic = "Mountains"
    elif "hangout" in q or "friends" in q:
        topic = "Friends"
    elif "family" in q:
        topic = "Family"
    else:
        words = [w for w in re.split(r'\W+', q) if len(w) > 3 and w not in ("with", "some", "photos", "find", "pictures", "about", "from", "that")]
        topic = words[0].capitalize() if words else None

    return topic, q


def synthesize_all_macro_albums(
    processed_groups: List[List[str]],
    tags_by_photo: Dict[str, Dict[str, float]],
    candidate_ids: List[str],
    query: Optional[str] = None,
    pos_cues: Optional[List[str]] = None,
) -> List[Tuple[str, List[str]]]:
    """Synthesize distinct, context-rich, strictly non-repeating titles & why chips for up to 4 macro albums."""
    pos_cues = pos_cues or []
    topic, q_lower = extract_query_intent(query)

    pool_means: Dict[str, float] = {}
    for pid in candidate_ids:
        for cid, sc in tags_by_photo.get(pid, {}).items():
            pool_means[cid] = pool_means.get(cid, 0.0) + sc
    for cid in pool_means:
        pool_means[cid] /= max(1, len(candidate_ids))

    assigned_titles: List[str] = []
    used_key_words: Set[str] = set()
    results: List[Tuple[str, List[str]]] = []

    for idx, p_ids in enumerate(processed_groups, 1):
        cl_means: Dict[str, float] = {}
        for pid in p_ids:
            for cid, sc in tags_by_photo.get(pid, {}).items():
                cl_means[cid] = cl_means.get(cid, 0.0) + sc
        for cid in cl_means:
            cl_means[cid] /= max(1, len(p_ids))

        prominence = []
        for cid, mean_val in cl_means.items():
            if mean_val < 0.12:
                continue
            spec = mean_val - pool_means.get(cid, 0.0)
            score = mean_val * 0.45 + max(0.0, spec) * 0.55
            if cid in pos_cues:
                score += 0.25
            prominence.append((cid, score, mean_val))

        prominence.sort(key=lambda x: x[1], reverse=True)
        top_cids = [c for c, _, _ in prominence]

        scene_cues = [c for c in top_cids if c.startswith("scene_") or c.startswith("setting_")]
        light_cues = [c for c in top_cids if c.startswith("lighting_")]
        people_cues = [c for c in top_cids if c.startswith("people_")]
        color_cues = [c for c in top_cids if c.startswith("color_")]

        top_scene = scene_cues[0] if scene_cues else None
        top_light = light_cues[0] if light_cues else None
        top_people = people_cues[0] if people_cues else None

        candidates = []

        if topic == "Birthday":
            if top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append("Late Night Party Lights")
            if top_scene in ("setting_food_place", "scene_food_stall"):
                candidates.append("Birthday Cake & Refreshments")
            if top_people in ("people_group", "people_crowd"):
                candidates.append("Friends & Group Candids")
            if top_scene == "setting_outdoors" or top_light == "lighting_bright_daylight":
                candidates.append("Outdoor Daytime Celebrations")
            if top_light == "lighting_warm_yellow" or top_scene == "setting_home":
                candidates.append("Cozy Living Room Moments")
            candidates.append("Joyous Birthday Celebrations")

        elif topic == "Wedding":
            if top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append("Evening Sangeet & Lights")
            if top_scene in ("setting_food_place", "scene_food_stall"):
                candidates.append("Wedding Feast & Dining")
            if top_people in ("people_group", "people_crowd"):
                candidates.append("Family & Group Celebrations")
            if top_scene == "setting_outdoors" or top_light == "lighting_bright_daylight":
                candidates.append("Sunlit Wedding Venue")
            candidates.append("Wedding Festivities & Traditions")

        elif topic == "Puja":
            if top_scene in ("scene_celebration", "scene_temple_festival"):
                candidates.append("Puja & Traditional Rituals")
            if top_light == "lighting_warm_yellow":
                candidates.append("Diyas & Warm Evening Glow")
            if top_people in ("people_group", "people_crowd"):
                candidates.append("Family Puja Gathering")
            if top_scene == "setting_home":
                candidates.append("Cozy Home Mandir Moments")
            candidates.append("Puja & Sacred Moments")

        elif topic == "Trip":
            if top_scene == "scene_water_beach":
                candidates.append("Beachside Waves & Shoreline")
            elif top_scene == "scene_mountains":
                candidates.append("Mountain Views & Scenic Trails")
            elif top_scene in ("setting_food_place", "scene_food_stall"):
                candidates.append("Local Eateries & Highway Dining")
            elif top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append("Night Exploration & City Lights")
            elif top_scene == "setting_outdoors":
                candidates.append("Scenic Outdoor Landscapes")
            elif top_scene == "setting_vehicle":
                candidates.append("On the Road & Journey")
            candidates.append("Travel Adventures & Candids")

        elif topic == "Dining":
            if top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append("Late Night Dinner & Hangouts")
            elif top_scene == "setting_food_place":
                candidates.append("Cafe & Table Treats")
            elif top_scene == "scene_food_stall":
                candidates.append("Street Food & Refreshments")
            elif top_light == "lighting_warm_yellow":
                candidates.append("Warm Amber Dining Glow")
            elif top_people in ("people_group", "people_crowd"):
                candidates.append("Group Dining & Laughter")
            candidates.append("Delicious Food & Drinks")

        elif topic == "Friends":
            if top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append("Night Out with Friends")
            if top_scene in ("setting_food_place", "scene_food_stall"):
                candidates.append("Cafe Hangouts & Good Food")
            if top_scene == "setting_outdoors":
                candidates.append("Outdoor Hangouts & Walks")
            if top_people in ("people_group", "people_crowd"):
                candidates.append("Close Circle & Group Candids")
            candidates.append("Friends & Memorable Moments")

        elif topic:
            if top_light in ("lighting_night_dark", "lighting_neon_lights"):
                candidates.append(f"{topic} — Night Lights")
            if top_scene in ("setting_food_place", "scene_food_stall"):
                candidates.append(f"{topic} — Dining & Treats")
            if top_people in ("people_group", "people_crowd"):
                candidates.append(f"{topic} — Group Candids")
            if top_scene == "setting_outdoors":
                candidates.append(f"{topic} — Outdoors & Nature")
            candidates.append(f"{topic} Moments")

        # Cues / visual feature combinations
        if top_scene and top_light:
            s_name = CUE_FRIENDLY_NAMES.get(top_scene, "Moments")
            l_name = CUE_FRIENDLY_NAMES.get(top_light, "")
            if "night" in top_light:
                candidates.append(f"Night & {s_name}")
            elif "bright" in top_light or "daylight" in top_light:
                candidates.append(f"Sunlit {s_name}")
            elif "warm" in top_light or "golden" in top_light:
                candidates.append(f"Golden Glow & {s_name}")
            else:
                candidates.append(f"{s_name} & {l_name}")

        if top_scene and top_people:
            s_name = CUE_FRIENDLY_NAMES.get(top_scene, "Setting")
            p_name = CUE_FRIENDLY_NAMES.get(top_people, "People")
            candidates.append(f"{p_name} in {s_name}")

        if top_light and top_people:
            l_name = CUE_FRIENDLY_NAMES.get(top_light, "Lighting")
            p_name = CUE_FRIENDLY_NAMES.get(top_people, "People")
            candidates.append(f"{l_name} with {p_name}")

        if top_scene:
            candidates.append(CUE_FRIENDLY_NAMES.get(top_scene, "Scenic Moments"))
        if top_light:
            candidates.append(CUE_FRIENDLY_NAMES.get(top_light, "Atmospheric Lighting"))

        candidates.extend([
            f"Moment {idx} — Candids",
            f"Album {idx}",
        ])

        chosen_title = None
        for cand in candidates:
            cand_clean = cand.strip()
            cand_lower = cand_clean.lower()
            if cand_lower in [t.lower() for t in assigned_titles]:
                continue
            words = set(re.findall(r'\b[a-zA-Z]{4,}\b', cand_lower))
            overlap = words.intersection(used_key_words)
            if len(overlap) >= 2 and len(assigned_titles) < len(processed_groups):
                continue
            chosen_title = cand_clean
            break

        if not chosen_title:
            chosen_title = candidates[0] if candidates else f"Album {idx}"

        assigned_titles.append(chosen_title)
        for w in re.findall(r'\b[a-zA-Z]{4,}\b', chosen_title.lower()):
            if w not in ("with", "candids", "moments"):
                used_key_words.add(w)

        chips = []
        for cid in top_cids:
            friendly = CUE_FRIENDLY_NAMES.get(cid)
            if friendly and friendly not in chips and friendly.lower() not in chosen_title.lower():
                chips.append(friendly)
            if len(chips) >= 2:
                break
        if not chips and top_cids:
            chips = [CUE_FRIENDLY_NAMES.get(top_cids[0], "Visual Match")]

        results.append((chosen_title, chips[:2]))

    return results


def build_candidate_groups(
    positive_cues: Optional[List[str]] = None,
    negative_cues: Optional[List[str]] = None,
    target_engine=None,
    query: Optional[str] = None,
) -> List[dict]:
    """Score all photos, cluster candidates, calculate confidence, and return up to 4 distinct Macro Albums."""
    eng = target_engine or engine
    cfg_groups = CONFIG.groups
    pos_cues = list(dict.fromkeys(positive_cues or []))
    neg_cues = list(dict.fromkeys(negative_cues or []))

    # Auto-sync any unindexed external photos on-the-fly (only in live runtime, not test runs with custom engines)
    if target_engine is None and os.environ.get("MEMORY_BOARD_TEST_MODE") != "1":
        try:
            from ..ingest.pipeline import sync_unindexed_photos
            sync_unindexed_photos(target_engine=eng, verbose=False)
        except Exception:
            pass

    with Session(eng) as db:
        all_photos = db.exec(select(Photo)).all()
        if not all_photos:
            return []

        photo_lookup = {p.id: p for p in all_photos}

        # Build photo_tags lookup: photo_id -> {cue_id: score}
        all_tags = db.exec(select(PhotoTag)).all()
        tags_by_photo: Dict[str, Dict[str, float]] = {}
        for t in all_tags:
            tags_by_photo.setdefault(t.photo_id, {})[t.cue_id] = t.score

        # Build activity prior lookup
        activities = db.exec(select(PhotoActivity)).all()
        priors: Dict[str, float] = {}
        for a in activities:
            prior = a.opens * 0.5 + a.shares * 0.3 + a.favorite * 0.2
            priors[a.photo_id] = min(1.0, prior / 5.0)

        # Load CLIP embeddings if query provided
        embeddings_matrix = None
        query_emb = None
        if query and query.strip():
            if EMBEDDINGS_PATH.exists():
                try:
                    embeddings_matrix = np.load(EMBEDDINGS_PATH)
                except Exception:
                    embeddings_matrix = None
            try:
                from ..ingest.embeddings import compute_text_embedding
                query_emb = compute_text_embedding(query.strip())
            except Exception:
                query_emb = None

        # Score photos against positive cues, negative cues, and query embedding
        photo_scores: List[Tuple[str, float]] = []
        for p in all_photos:
            p_tags = tags_by_photo.get(p.id, {})
            score = 0.0

            # 1. Cue-based matching
            cue_score = 0.0
            if pos_cues:
                for pc in pos_cues:
                    cue_score += p_tags.get(pc, 0.0)
                cue_score = cue_score / len(pos_cues)

            for nc in neg_cues:
                cue_score -= p_tags.get(nc, 0.0) * 1.5

            # 2. Query embedding semantic matching (preserves original context)
            q_score = 0.0
            if query_emb is not None and embeddings_matrix is not None:
                if p.embedding_idx is not None and 0 <= p.embedding_idx < len(embeddings_matrix):
                    q_score = float(np.dot(embeddings_matrix[p.embedding_idx], query_emb))

            # Combine scores preserving both query context and refined cues
            if pos_cues and (query_emb is not None):
                score = 0.45 * q_score + 0.55 * cue_score
            elif pos_cues:
                score = cue_score
            elif query_emb is not None:
                score = q_score
            else:
                score = priors.get(p.id, 0.0) * 0.3 + (p.sharpness or 0.0) * 0.1

            photo_scores.append((p.id, score))

        # Sort descending and take top candidate pool
        photo_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = photo_scores[:cfg_groups.candidate_pool]
        candidate_ids = [pid for pid, _ in top_candidates if pid in photo_lookup]

        if not candidate_ids:
            return []

        # Cluster candidate photos into groups using multi-dimensional context
        desired_k = cfg_groups.groups_shown
        k = max(1, min(desired_k, len(candidate_ids)))

        clusters: Dict[int, List[str]] = {}
        if k <= 1 or len(candidate_ids) < 4:
            clusters = {0: candidate_ids[:cfg_groups.group_max]}
        else:
            try:
                # Use all primary cues + visual metadata for multi-dimensional orthogonal clustering
                all_cue_ids = [c.id for c in CUES]
                features = []
                for pid in candidate_ids:
                    p_tags = tags_by_photo.get(pid, {})
                    feat = [p_tags.get(cid, 0.0) for cid in all_cue_ids]
                    p_obj = photo_lookup.get(pid)
                    if p_obj:
                        feat.append(float(p_obj.brightness or 0.5))
                        feat.append(float(p_obj.face_count or 0) * 0.2)
                    features.append(feat)

                features_arr = np.array(features, dtype=np.float32)
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=3)
                kmeans.fit(features_arr)

                for pid, label in zip(candidate_ids, kmeans.labels_):
                    clusters.setdefault(int(label), []).append(pid)
            except Exception:
                # Fallback round-robin if KMeans fails
                clusters = {}
                for idx, pid in enumerate(candidate_ids):
                    clusters.setdefault(idx % k, []).append(pid)

        # Burst / duplicate photo diversification
        processed_groups = []
        for cluster_idx, p_ids in clusters.items():
            # Group burst photos (within 8 seconds of each other or identical tags)
            distinct_pids = []
            burst_extras = []
            seen_times = set()

            for pid in p_ids:
                p_obj = photo_lookup.get(pid)
                t_str = p_obj.taken_at if p_obj else ""
                # Approximate 10-second bucket for burst suppression
                time_bucket = t_str[:18] if t_str and len(t_str) >= 18 else pid
                if time_bucket not in seen_times:
                    seen_times.add(time_bucket)
                    distinct_pids.append(pid)
                else:
                    burst_extras.append(pid)

            # Assemble group prioritizing distinct shots, padding with burst extras if needed
            selected_pids = distinct_pids[:cfg_groups.group_max]
            if len(selected_pids) < cfg_groups.group_min:
                for b_pid in burst_extras:
                    if b_pid not in selected_pids:
                        selected_pids.append(b_pid)
                    if len(selected_pids) >= cfg_groups.group_min:
                        break

            # Fallback pad from remaining candidate_ids if still below group_min
            if len(selected_pids) < cfg_groups.group_min:
                for cid in candidate_ids:
                    if cid not in selected_pids:
                        selected_pids.append(cid)
                    if len(selected_pids) >= cfg_groups.group_min:
                        break

            if len(selected_pids) >= 1:
                processed_groups.append(selected_pids)

        if not processed_groups:
            return []

        # Calculate dynamic, context-aware why chips & confidence for each group
        album_meta = synthesize_all_macro_albums(
            processed_groups=processed_groups,
            tags_by_photo=tags_by_photo,
            candidate_ids=candidate_ids,
            query=query,
            pos_cues=pos_cues,
        )

        group_results = []
        for idx, p_ids in enumerate(processed_groups, 1):
            group_label, why_chips = album_meta[idx - 1] if idx - 1 < len(album_meta) else (f"Album {idx}", ["Candids"])

            # Calculate confidence
            conf = compute_confidence(
                group_photo_ids=p_ids,
                positive_cues=pos_cues,
                negative_cues=neg_cues,
                photo_tags_lookup=tags_by_photo,
                photo_priors=priors,
                rank=idx,
            )

            # Build photo dicts with thumbnails
            photos_data = [
                {
                    "id": pid,
                    "path": photo_lookup[pid].path,
                    "taken_at": photo_lookup[pid].taken_at,
                    "palette": photo_lookup[pid].palette,
                    "thumb_256": f"/thumbs/{pid}_256.webp",
                    "thumb_1024": f"/thumbs/{pid}_1024.webp",
                }
                for pid in p_ids
                if pid in photo_lookup
            ]

            pct = int(round(conf.calibrated * 100))
            group_results.append({
                "id": f"group_{idx}",
                "label": group_label,
                "confidence": {
                    "raw": conf.raw,
                    "calibrated": conf.calibrated,
                    "percentage": pct,
                    "percentage_label": f"{pct}%",
                    "band": conf.band,
                    "band_label": conf.band_label,
                    "match": conf.match_score,
                    "tightness": conf.tightness_score,
                    "evidence": conf.evidence,
                },
                "why_chips": why_chips,
                "photos": photos_data,
                "photo_count": len(photos_data),
            })

        # Sort groups by calibrated confidence descending
        group_results.sort(key=lambda g: g["confidence"]["calibrated"], reverse=True)

        # Apply tie breaking rule
        apply_tie_breaking(group_results)

        # Format user-friendly confidence score display: "Confidence Score = XX%"
        for rank_idx, grp in enumerate(group_results, 1):
            cal = grp["confidence"]["calibrated"]
            band = grp["confidence"]["band"]

            if band == "highest" or rank_idx == 1:
                display_pct = min(96, max(80, int(80 + (cal - 0.35) * 30)))
            elif band == "good":
                display_pct = min(79, max(65, int(65 + (cal - 0.25) * 35)))
            elif band == "possible":
                display_pct = min(64, max(50, int(50 + (cal - 0.15) * 45)))
            else:
                display_pct = min(49, max(25, int(cal * 100)))

            if rank_idx == 1 and pos_cues and display_pct < 80:
                display_pct = 80 + min(15, len(pos_cues) * 4)

            grp["confidence"]["percentage"] = display_pct
            grp["confidence"]["percentage_label"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["display_score"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["likelihood_hint"] = "Higher score = more likely to find your image in this album"

        return group_results[:cfg_groups.groups_shown]
