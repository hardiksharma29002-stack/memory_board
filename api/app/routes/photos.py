"""Photos API route for timeline photo browsing and mobile/desktop photo uploads."""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlmodel import Session, select, delete

from ..config import PHOTOS_DIR, THUMBS_DIR, DB_PATH, EMBEDDINGS_PATH, DATA_DIR
from ..database import get_session, engine
from ..models import Photo, PhotoTag, PhotoActivity
from ..ingest.pipeline import run_ingestion

router = APIRouter(prefix="/api/photos", tags=["photos"])

SAMPLE_BACKUP_DIR = DATA_DIR / "sample_backup"
LIBRARY_PHOTO_CAP = 500


@router.get("/stats")
def get_photo_stats(db: Session = Depends(get_session)):
    """Return library statistics including total photos, cap, and recommendation nudge."""
    total = db.exec(select(Photo)).all()
    count = len(total)
    has_samples = False
    if SAMPLE_BACKUP_DIR.exists():
        has_samples = len(list(SAMPLE_BACKUP_DIR.glob("*"))) > 0

    return {
        "total_photos": count,
        "cap": LIBRARY_PHOTO_CAP,
        "available_slots": max(0, LIBRARY_PHOTO_CAP - count),
        "nudge_message": "Add ~100 real photos for a real retrieval experience! (Library cap: 500 photos)",
        "has_sample_backup": has_samples,
    }


@router.post("/upload")
async def upload_photos(
    files: List[UploadFile] = File(...),
    replace: bool = Form(False),
    db: Session = Depends(get_session),
):
    """Upload user photos directly from mobile photo gallery or file picker.

    - Supports multiple photos with native mobile gallery access.
    - Capped at 500 photos total.
    - Option to replace demo photos or append.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No photo files provided.")

    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    # If replace is requested, wipe existing database entries and files
    if replace:
        with Session(engine) as sess:
            sess.exec(delete(PhotoTag))
            sess.exec(delete(PhotoActivity))
            sess.exec(delete(Photo))
            sess.commit()

        for f in PHOTOS_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass

        for f in THUMBS_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass

        if EMBEDDINGS_PATH.exists():
            try:
                EMBEDDINGS_PATH.unlink()
            except Exception:
                pass

    current_photos = [
        f for f in PHOTOS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    current_count = len(current_photos)
    available_slots = max(0, LIBRARY_PHOTO_CAP - current_count)

    if available_slots == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Library photo cap ({LIBRARY_PHOTO_CAP}) reached. Please select 'Replace' to clear existing photos.",
        )

    files_to_save = files[:available_slots]
    saved_files = []

    for file in files_to_save:
        safe_name = Path(file.filename or f"upload_{int(time.time()*1000)}.jpg").name
        dest_path = PHOTOS_DIR / safe_name

        counter = 1
        stem = dest_path.stem
        suffix = dest_path.suffix or ".jpg"
        while dest_path.exists():
            dest_path = PHOTOS_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

        contents = await file.read()
        if len(contents) > 0:
            with open(dest_path, "wb") as f_out:
                f_out.write(contents)
            saved_files.append(dest_path)

    # Run ingestion pipeline to compute thumbs, EXIF, palettes, faces, CLIP embeddings & tags
    stats = run_ingestion(photos_dir=PHOTOS_DIR, target_engine=engine, verbose=False)

    new_total = len([
        f for f in PHOTOS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ])

    return {
        "status": "success",
        "uploaded_count": len(saved_files),
        "indexed_count": stats.get("processed", 0),
        "total_photos": new_total,
        "cap": LIBRARY_PHOTO_CAP,
        "message": f"Successfully indexed {len(saved_files)} photos! Total library: {new_total} / {LIBRARY_PHOTO_CAP}.",
    }


@router.post("/reset-sample")
def reset_to_sample_photos():
    """Reset the photo library back to the default 400 sample photos."""
    if not SAMPLE_BACKUP_DIR.exists():
        raise HTTPException(status_code=404, detail="Sample photos backup not found.")

    with Session(engine) as sess:
        sess.exec(delete(PhotoTag))
        sess.exec(delete(PhotoActivity))
        sess.exec(delete(Photo))
        sess.commit()

    for f in PHOTOS_DIR.iterdir():
        if f.is_file():
            try:
                f.unlink()
            except Exception:
                pass

    for f in SAMPLE_BACKUP_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, PHOTOS_DIR / f.name)

    stats = run_ingestion(photos_dir=PHOTOS_DIR, target_engine=engine, verbose=False)

    return {
        "status": "success",
        "total_photos": stats.get("total", 0),
        "message": "Library successfully reset to default sample photos.",
    }


@router.get("")
def list_photos(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    """Retrieve indexed photos for timeline view, ordered chronologically."""
    statement = (
        select(Photo)
        .where(Photo.in_trash == 0, Photo.archived == 0)
        .order_by(Photo.taken_at.desc())
        .offset(offset)
        .limit(limit)
    )
    photos = db.exec(statement).all()

    return {
        "photos": [
            {
                "id": p.id,
                "path": p.path,
                "taken_at": p.taken_at,
                "hour_bucket": p.hour_bucket,
                "width": p.width,
                "height": p.height,
                "palette": p.palette,
                "source": p.source,
                "thumb_256": f"/thumbs/{p.id}_256.webp",
                "thumb_1024": f"/thumbs/{p.id}_1024.webp",
            }
            for p in photos
        ],
        "total": len(photos),
        "offset": offset,
        "limit": limit,
    }


@router.get("/{photo_id}")
def get_photo(photo_id: str, db: Session = Depends(get_session)):
    """Retrieve full metadata for a single photo."""
    photo = db.get(Photo, photo_id)
    if not photo:
        return {"error": "Photo not found"}

    return {
        "id": photo.id,
        "path": photo.path,
        "taken_at": photo.taken_at,
        "hour_bucket": photo.hour_bucket,
        "width": photo.width,
        "height": photo.height,
        "palette": photo.palette,
        "source": photo.source,
        "thumb_256": f"/thumbs/{photo.id}_256.webp",
        "thumb_1024": f"/thumbs/{photo.id}_1024.webp",
    }
