"""Activity REST API endpoint for recording photo interactions."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models import Photo, PhotoActivity

router = APIRouter(prefix="/api/activity", tags=["activity"])


class ActivityRequest(BaseModel):
    photo_id: str
    kind: str  # "open" | "share" | "favorite"


@router.post("")
def record_activity(req: ActivityRequest, db: Session = Depends(get_session)):
    """Record an interaction (open, share, favorite) on a photo for behaviour prior computation."""
    photo = db.get(Photo, req.photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    activity = db.get(PhotoActivity, req.photo_id)
    if not activity:
        activity = PhotoActivity(photo_id=req.photo_id, opens=0, shares=0, favorite=0)
        db.add(activity)

    now_iso = datetime.now(timezone.utc).isoformat()

    if req.kind == "open":
        activity.opens += 1
        activity.last_opened_at = now_iso
    elif req.kind == "share":
        activity.shares += 1
    elif req.kind == "favorite":
        activity.favorite = 1 if activity.favorite == 0 else 0  # toggle favorite
    else:
        raise HTTPException(status_code=400, detail=f"Invalid activity kind: '{req.kind}'. Must be 'open', 'share', or 'favorite'.")

    db.commit()
    db.refresh(activity)

    return {
        "status": "ok",
        "photo_id": activity.photo_id,
        "opens": activity.opens,
        "shares": activity.shares,
        "favorite": activity.favorite,
        "last_opened_at": activity.last_opened_at,
    }
