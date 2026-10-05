"""Next-wave (v1.1 / Phase 7) engine features.

All features are feature-flagged and designed to be modular.
- Hiding places check (trash, archive, locked, un-backed-up)
- Who-was-there co-occurrence row (face counts only, no biometrics)
- Paint-it palette matching (Delta E in RGB/Lab space)
- Timeline landmark moments segmentation
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlmodel import Session, select

from ..database import engine
from ..models import Photo, PhotoTag


def check_hiding_places(target_engine=None) -> Dict[str, Any]:
    """Check simulated hiding places: trash, archived, locked, and unbacked up."""
    eng = target_engine or engine
    with Session(eng) as db:
        trash = db.exec(select(Photo).where(Photo.in_trash == 1)).all()
        archived = db.exec(select(Photo).where(Photo.archived == 1)).all()
        locked = db.exec(select(Photo).where(Photo.locked == 1)).all()
        unbacked = db.exec(select(Photo).where(Photo.backed_up == 0)).all()

    return {
        "trash": {
            "count": len(trash),
            "message": f"{len(trash)} photos found in Trash (items in Trash are deleted after 30 days)." if trash else "No photos in Trash.",
            "photo_ids": [p.id for p in trash],
        },
        "archive": {
            "count": len(archived),
            "message": f"{len(archived)} photos found in Archive." if archived else "No photos in Archive.",
            "photo_ids": [p.id for p in archived],
        },
        "locked": {
            "count": len(locked),
            "message": f"{len(locked)} photos found in Locked Folder." if locked else "No photos in Locked Folder.",
            "photo_ids": [p.id for p in locked],
        },
        "unbacked": {
            "count": len(unbacked),
            "message": f"{len(unbacked)} photos not yet backed up to cloud." if unbacked else "All photos backed up.",
            "photo_ids": [p.id for p in unbacked],
        },
    }


def get_who_was_there_options(candidate_photo_ids: List[str], target_engine=None) -> List[Dict[str, Any]]:
    """Derive who-was-there face count buckets from the candidate set (strictly no biometrics)."""
    eng = target_engine or engine
    with Session(eng) as db:
        photos = db.exec(
            select(Photo).where(Photo.id.in_(candidate_photo_ids))
        ).all()

    counts = {
        "solo": 0,    # face_count == 1
        "duo": 0,     # face_count == 2
        "group": 0,   # face_count in 3..5
        "crowd": 0,   # face_count >= 6
    }
    for p in photos:
        fc = p.face_count
        if fc == 1:
            counts["solo"] += 1
        elif fc == 2:
            counts["duo"] += 1
        elif 3 <= fc <= 5:
            counts["group"] += 1
        elif fc >= 6:
            counts["crowd"] += 1

    return [
        {"id": "people_just_me", "label": "Just me", "count": counts["solo"]},
        {"id": "people_2_people", "label": "2 people", "count": counts["duo"]},
        {"id": "people_3_5_people", "label": "3 to 5 people", "count": counts["group"]},
        {"id": "people_big_crowd", "label": "Big crowd", "count": counts["crowd"]},
    ]


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (e.g. #FFAA00) to RGB tuple."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) != 6:
        return (128, 128, 128)
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def rgb_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Euclidean distance between two RGB colors (0 to ~441)."""
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2)


def match_paint_it_palette(
    target_hex_colors: List[str],
    day_night: Optional[str] = None,  # "day" | "night"
    target_engine=None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Match photos by color palette distance and day/night time filter."""
    eng = target_engine or engine
    target_rgbs = [hex_to_rgb(h) for h in target_hex_colors]

    with Session(eng) as db:
        photos = db.exec(select(Photo).where(Photo.in_trash == 0, Photo.archived == 0)).all()

        scored = []
        for p in photos:
            # Time filter if specified
            if day_night == "day" and p.hour_bucket is not None and not (6 <= p.hour_bucket <= 18):
                continue
            if day_night == "night" and p.hour_bucket is not None and (6 <= p.hour_bucket <= 18):
                continue

            try:
                palette = json.loads(p.palette or "[]")
            except Exception:
                palette = []

            if not palette or not target_rgbs:
                score = 0.5
            else:
                photo_rgbs = [hex_to_rgb(h) for h in palette]
                # Min distance across photo palette to any target color
                dists = [
                    min(rgb_distance(prgb, trgb) for prgb in photo_rgbs)
                    for trgb in target_rgbs
                ]
                mean_dist = sum(dists) / len(dists)
                score = max(0.0, 1.0 - (mean_dist / 255.0))

            scored.append((p, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [p for p, _ in scored[:limit]]

        return [
            {
                "id": p.id,
                "path": p.path,
                "taken_at": p.taken_at,
                "palette": p.palette,
                "thumb_256": f"/thumbs/{p.id}_256.webp",
                "thumb_1024": f"/thumbs/{p.id}_1024.webp",
            }
            for p in top
        ]


def segment_timeline_moments(target_engine=None, gap_hours: float = 6.0) -> List[Dict[str, Any]]:
    """Segment timeline photos into moments when timestamp gap exceeds threshold."""
    eng = target_engine or engine
    with Session(eng) as db:
        photos = db.exec(
            select(Photo)
            .where(Photo.taken_at.is_not(None), Photo.in_trash == 0)
            .order_by(Photo.taken_at.asc())
        ).all()

    if not photos:
        return []

    moments = []
    current_moment = [photos[0]]

    from datetime import datetime
    for p in photos[1:]:
        try:
            prev_t = datetime.fromisoformat(current_moment[-1].taken_at)
            curr_t = datetime.fromisoformat(p.taken_at)
            diff_h = (curr_t - prev_t).total_seconds() / 3600.0
        except Exception:
            diff_h = 0.0

        if diff_h > gap_hours:
            moments.append({
                "moment_id": f"m_{len(moments) + 1}",
                "start_time": current_moment[0].taken_at,
                "end_time": current_moment[-1].taken_at,
                "photo_count": len(current_moment),
                "cover_photo_id": current_moment[0].id,
            })
            current_moment = [p]
        else:
            current_moment.append(p)

    if current_moment:
        moments.append({
            "moment_id": f"m_{len(moments) + 1}",
            "start_time": current_moment[0].taken_at,
            "end_time": current_moment[-1].taken_at,
            "photo_count": len(current_moment),
            "cover_photo_id": current_moment[0].id,
        })

    return moments
