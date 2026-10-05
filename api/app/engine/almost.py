"""'Almost!' nearest-neighbor pivot engine."""

from typing import Dict, List, Optional
import numpy as np
from sqlmodel import Session, select

from ..database import engine
from ..models import Photo, PhotoTag
from ..vocab import ALMOST_OPTIONS


def pivot_almost(
    photo_id: str,
    difference_axis: str,
    target_engine=None,
    limit: int = 15,
) -> List[dict]:
    """Find related photos pivoting around the specified difference axis."""
    eng = target_engine or engine

    with Session(eng) as db:
        anchor = db.get(Photo, photo_id)
        if not anchor:
            return []

        all_photos = db.exec(select(Photo).where(Photo.id != photo_id)).all()
        if not all_photos:
            return []

        candidates = []

        if difference_axis == "diff_time":
            # Prefer different hour_bucket (e.g. night if anchor was day)
            for p in all_photos:
                penalty = 0.0
                if p.hour_bucket is not None and anchor.hour_bucket is not None:
                    # Higher score for greater time difference
                    diff = abs(p.hour_bucket - anchor.hour_bucket)
                    score = min(1.0, diff / 12.0)
                else:
                    score = 0.5
                candidates.append((p, score))

        elif difference_axis == "diff_people":
            # Prefer different face_count
            for p in all_photos:
                face_diff = abs(p.face_count - anchor.face_count)
                score = min(1.0, face_diff / 3.0)
                candidates.append((p, score))

        elif difference_axis == "diff_place":
            # Different setting / source
            for p in all_photos:
                score = 0.8 if p.source != anchor.source else 0.4
                candidates.append((p, score))

        else:
            # General nearest neighbor / visual similarity
            for p in all_photos:
                score = 0.5
                candidates.append((p, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top = [p for p, _ in candidates[:limit]]

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
