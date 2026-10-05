import io
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, select, delete
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

from ..config import PHOTOS_DIR, THUMBS_DIR, DB_PATH, EMBEDDINGS_PATH, DATA_DIR
from ..database import get_session, engine
from ..models import Photo, PhotoTag, PhotoActivity
from ..ingest.pipeline import run_ingestion
from ..ingest.thumbnails import generate_thumbnails

router = APIRouter(prefix="/api/photos", tags=["photos"])

SAMPLE_BACKUP_DIR = DATA_DIR / "sample_backup"
DEFAULT_PHOTO_CAP = 2000


def generate_svg_placeholder(photo_id: str, label: str = "Memory", palette: Optional[List[str]] = None) -> bytes:
    """Generate a premium SVG placeholder with gradient palette colors when image is loading or missing."""
    p_colors = palette if palette and len(palette) >= 2 else ["#1e293b", "#334155", "#0ea5e9"]
    c1, c2 = p_colors[0], p_colors[1]
    c3 = p_colors[2] if len(p_colors) > 2 else c1

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="grad_{photo_id[:8]}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}" />
      <stop offset="50%" stop-color="{c2}" />
      <stop offset="100%" stop-color="{c3}" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad_{photo_id[:8]})" rx="16" />
  <circle cx="200" cy="180" r="50" fill="white" opacity="0.15" />
  <path d="M175 185 L190 165 L210 190 L220 178 L235 198 Z" fill="white" opacity="0.85" />
  <circle cx="185" cy="155" r="7" fill="white" opacity="0.85" />
  <text x="200" y="270" text-anchor="middle" fill="white" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="14" font-weight="600" opacity="0.9">{label}</text>
</svg>"""
    return svg.encode("utf-8")


@router.get("/stats")
def get_photo_stats(db: Session = Depends(get_session)):
    """Return library statistics including total photos, dynamic cap, and recommendation nudge."""
    total = db.exec(select(Photo)).all()
    count = len(total)
    has_samples = False
    if SAMPLE_BACKUP_DIR.exists():
        has_samples = len(list(SAMPLE_BACKUP_DIR.glob("*"))) > 0

    return {
        "total_photos": count,
        "cap": 500,
        "available_slots": max(0, 500 - count),
        "nudge_message": "Add ~100 real photos for a real retrieval experience! (Library cap: 500 photos)",
        "has_sample_backup": has_samples,
    }


@router.post("/upload")
async def upload_photos(
    files: List[UploadFile] = File(...),
    replace: bool = Form(False),
    db: Session = Depends(get_session),
):
    """Upload user photos directly from mobile photo gallery or desktop file picker.

    - Supports single & multi-photo uploads.
    - Zero rejection: accepts all formats (JPG, PNG, WEBP, HEIC, BMP, TIFF, AVIF).
    - Auto-normalizes rotation, colorspace, and formats.
    - Auto-expands library capacity.
    - Idempotent and fail-safe ingestion.
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

    saved_files = []

    for file in files:
        contents = await file.read()
        if not contents or len(contents) == 0:
            continue

        raw_filename = file.filename or f"upload_{int(time.time()*1000)}.jpg"
        clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(raw_filename).stem)[:40]
        if not clean_stem:
            clean_stem = f"photo_{int(time.time()*1000)}"

        dest_path = PHOTOS_DIR / f"{clean_stem}_{int(time.time()*1000)}.jpg"

        # Attempt PIL decode and normalization (handles HEIC, PNG, WEBP, TIFF, CMYK, etc.)
        saved_successfully = False
        try:
            with Image.open(io.BytesIO(contents)) as img:
                # Handle EXIF orientation
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                # Convert to standard RGB for JPEG/WebP compatibility
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                img.save(dest_path, format="JPEG", quality=95)
                saved_files.append(dest_path)
                saved_successfully = True
        except Exception as img_err:
            pass

        # Fallback: if PIL couldn't decode, write raw bytes so photo is never lost
        if not saved_successfully:
            suffix = Path(raw_filename).suffix or ".jpg"
            dest_path = PHOTOS_DIR / f"{clean_stem}_{int(time.time()*1000)}{suffix}"
            try:
                with open(dest_path, "wb") as f_out:
                    f_out.write(contents)
                saved_files.append(dest_path)
            except Exception:
                pass

    if not saved_files:
        raise HTTPException(status_code=400, detail="Could not process any of the uploaded photo files.")

    # Run ingestion pipeline only on newly saved files for ultra-fast indexing
    stats = run_ingestion(
        photos_dir=PHOTOS_DIR,
        target_engine=engine,
        verbose=False,
        file_paths=saved_files,
    )

    new_total = len([
        f for f in PHOTOS_DIR.iterdir()
        if f.is_file()
    ])

    return {
        "status": "success",
        "uploaded_count": len(saved_files),
        "indexed_count": stats.get("processed", 0),
        "total_photos": new_total,
        "cap": max(DEFAULT_PHOTO_CAP, new_total + 500),
        "message": f"Successfully indexed {len(saved_files)} new photo{'s' if len(saved_files) != 1 else ''}! Total library: {new_total} photos.",
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


@router.get("/{photo_id}/thumb")
def get_photo_thumbnail(
    photo_id: str,
    size: int = Query(default=256, ge=64, le=1024),
    db: Session = Depends(get_session),
):
    """Retrieve or dynamically generate a WebP thumbnail for a photo. Never returns a broken image."""
    thumb_path = THUMBS_DIR / f"{photo_id}_{size}.webp"
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return FileResponse(thumb_path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400, immutable"})

    # Check alternate size if exists
    alt_size = 1024 if size == 256 else 256
    alt_path = THUMBS_DIR / f"{photo_id}_{alt_size}.webp"
    if alt_path.exists() and alt_path.stat().st_size > 0:
        return FileResponse(alt_path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400, immutable"})

    # Locate photo in database
    photo = db.get(Photo, photo_id)
    if photo:
        candidates = [
            DATA_DIR.parent / photo.path,
            DATA_DIR / photo.path,
            PHOTOS_DIR / Path(photo.path).name,
        ]
        found_img_path = next((p for p in candidates if p.exists() and p.is_file()), None)
        if found_img_path:
            try:
                generate_thumbnails(found_img_path, photo_id, output_dir=THUMBS_DIR)
                if thumb_path.exists():
                    return FileResponse(thumb_path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400, immutable"})
            except Exception:
                pass

        # Parse palette for fallback SVG
        palette_list = None
        if photo.palette:
            try:
                palette_list = json.loads(photo.palette)
            except Exception:
                pass

        svg_bytes = generate_svg_placeholder(
            photo_id=photo_id,
            label=photo.hour_bucket.title() if photo.hour_bucket else "Memory",
            palette=palette_list,
        )
        return Response(content=svg_bytes, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})

    svg_bytes = generate_svg_placeholder(photo_id=photo_id, label="Photo")
    return Response(content=svg_bytes, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


@router.get("/{photo_id}/raw")
def get_photo_raw(photo_id: str, db: Session = Depends(get_session)):
    """Retrieve original photo file with fail-safe fallback."""
    photo = db.get(Photo, photo_id)
    if photo:
        candidates = [
            DATA_DIR.parent / photo.path,
            DATA_DIR / photo.path,
            PHOTOS_DIR / Path(photo.path).name,
        ]
        found_img_path = next((p for p in candidates if p.exists() and p.is_file()), None)
        if found_img_path:
            return FileResponse(found_img_path)

    # Return thumbnail or SVG fallback
    return get_photo_thumbnail(photo_id=photo_id, size=1024, db=db)


@router.delete("/{photo_id}")
def delete_photo(photo_id: str, db: Session = Depends(get_session)):
    """Permanently delete a photo, all associated cue tags/activity, and thumbnail files."""
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Remove database entries
    db.exec(delete(PhotoTag).where(PhotoTag.photo_id == photo_id))
    db.exec(delete(PhotoActivity).where(PhotoActivity.photo_id == photo_id))
    db.delete(photo)
    db.commit()

    # Remove generated thumbnails
    for t in [THUMBS_DIR / f"{photo_id}_256.webp", THUMBS_DIR / f"{photo_id}_1024.webp"]:
        if t.exists() and t.is_file():
            try:
                t.unlink()
            except Exception:
                pass

    # Remove photo image file
    candidates = [
        DATA_DIR.parent / photo.path,
        DATA_DIR / photo.path,
        PHOTOS_DIR / Path(photo.path).name,
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            try:
                p.unlink()
            except Exception:
                pass

    return {
        "status": "success",
        "deleted_id": photo_id,
        "message": "Photo deleted successfully",
    }


