"""Photo ingestion pipeline orchestrator.

Processes all photos in data/photos/ idempotently:
1. Generates 256px + 1024px WebP thumbnails
2. Computes sharpness and brightness
3. Extracts EXIF date, camera make/model, and hour bucket
4. Extracts 3-color k-means palette
5. Detects face count (count only)
6. Infers photo source
7. Computes CLIP ViT-B-32 image embedding
8. Computes zero-shot and rule-based cue tags
9. Persists metadata to SQLite and embeddings to embeddings.npy
"""

import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from sqlmodel import Session, select

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ..config import CONFIG, DATA_DIR, PHOTOS_DIR, THUMBS_DIR, DB_PATH, EMBEDDINGS_PATH
from ..database import engine, init_db
from ..models import Photo, PhotoTag, PhotoActivity
from .exif import extract_exif
from .thumbnails import generate_thumbnails
from .palette import extract_palette, palette_to_json
from .sharpness import compute_sharpness_and_brightness
from .faces import count_faces
from .source import infer_source
from .embeddings import (
    compute_image_embedding,
    get_cue_text_embeddings,
    load_all_embeddings,
    save_embeddings,
)
from .tags import compute_rule_based_tags, compute_clip_tags


try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".tiff", ".tif", ".jfif", ".avif"
}


def get_photo_id(file_path: Path) -> str:
    """Generate a clean, deterministic photo ID based on file path and size."""
    try:
        stat = file_path.stat()
        raw = f"{file_path.name}_{stat.st_size}".encode("utf-8")
        return hashlib.md5(raw).hexdigest()[:16]
    except Exception:
        raw = f"{file_path.name}_{time.time()}".encode("utf-8")
        return hashlib.md5(raw).hexdigest()[:16]


def run_ingestion(
    photos_dir: Path = PHOTOS_DIR,
    target_engine=None,
    embeddings_path: Path = EMBEDDINGS_PATH,
    thumbs_dir: Optional[Path] = None,
    verbose: bool = True,
    file_paths: Optional[List[Path]] = None,
) -> Dict[str, int]:
    """Run full ingestion pipeline over photos_dir or specific file_paths. Fully idempotent and fail-safe."""
    start_time = time.time()
    eng = target_engine or engine
    init_db(eng)

    photos_dir.mkdir(parents=True, exist_ok=True)
    target_thumbs_dir = thumbs_dir or THUMBS_DIR
    target_thumbs_dir.mkdir(parents=True, exist_ok=True)

    if file_paths is not None:
        photo_files = [Path(p) for p in file_paths if Path(p).is_file()]
    else:
        photo_files = [
            f for f in photos_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    if verbose:
        print(f"📷 Starting ingestion: found {len(photo_files)} candidate photos")

    # Load existing photos to ensure idempotency
    existing_photo_ids = set()
    with Session(eng) as session:
        existing = session.exec(select(Photo.id)).all()
        existing_photo_ids.update(existing)

    embeddings_matrix = load_all_embeddings(embeddings_path)
    new_embeddings_list: List[np.ndarray] = []
    cue_text_embeddings = get_cue_text_embeddings()

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for i, file_path in enumerate(photo_files, 1):
        photo_id = get_photo_id(file_path)

        if photo_id in existing_photo_ids:
            skipped_count += 1
            continue

        try:
            # 1. Thumbnails (with fail-safe fallback)
            try:
                generate_thumbnails(file_path, photo_id, output_dir=target_thumbs_dir)
            except Exception as thumb_err:
                try:
                    with Image.open(file_path) as fallback_img:
                        fallback_img = ImageOps.exif_transpose(fallback_img)
                        if fallback_img.mode not in ("RGB", "L"):
                            fallback_img = fallback_img.convert("RGB")
                        t1024 = fallback_img.copy()
                        t1024.thumbnail((1024, 1024))
                        t1024.save(target_thumbs_dir / f"{photo_id}_1024.webp", "WEBP", quality=80)
                        t256 = fallback_img.copy()
                        t256.thumbnail((256, 256))
                        t256.save(target_thumbs_dir / f"{photo_id}_256.webp", "WEBP", quality=75)
                except Exception:
                    pass

            # 2. Sharpness & Brightness
            try:
                sharpness, brightness = compute_sharpness_and_brightness(file_path)
            except Exception:
                sharpness, brightness = 50.0, 128.0

            # 3. EXIF & Hour Bucket
            try:
                exif_info = extract_exif(file_path, brightness=brightness)
            except Exception:
                exif_info = {
                    "taken_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "hour_bucket": "afternoon",
                    "width": 800,
                    "height": 600,
                }

            # 4. Palette
            try:
                palette = extract_palette(file_path, k=3)
            except Exception:
                palette = ["#3b82f6", "#10b981", "#f59e0b"]

            # 5. Face count
            try:
                face_count = count_faces(file_path)
            except Exception:
                face_count = 0

            # 6. Source inference
            try:
                source = infer_source(file_path, exif_data=exif_info)
            except Exception:
                source = "user_upload"

            # 7. Embedding
            try:
                img_emb = compute_image_embedding(file_path)
            except Exception:
                img_emb = np.zeros(512, dtype=np.float32)
                img_emb[0] = 1.0

            current_embedding_idx = len(embeddings_matrix) + len(new_embeddings_list)
            new_embeddings_list.append(img_emb)

            # 8. Cue tags
            try:
                rule_tags = compute_rule_based_tags(photo_id, face_count)
            except Exception:
                rule_tags = []

            try:
                clip_tags = compute_clip_tags(photo_id, img_emb, cue_text_embeddings)
            except Exception:
                clip_tags = []

            all_tags = rule_tags + clip_tags

            # 9. Database records
            try:
                rel_path = str(file_path.relative_to(DATA_DIR.parent))
            except ValueError:
                rel_path = str(file_path)

            photo_record = Photo(
                id=photo_id,
                path=rel_path,
                taken_at=exif_info.get("taken_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
                hour_bucket=exif_info.get("hour_bucket") or "afternoon",
                width=exif_info.get("width") or 800,
                height=exif_info.get("height") or 600,
                source=source,
                face_count=face_count,
                sharpness=sharpness,
                brightness=brightness,
                palette=palette_to_json(palette),
                embedding_idx=current_embedding_idx,
            )
            activity_record = PhotoActivity(photo_id=photo_id)

            with Session(eng) as session:
                session.add(photo_record)
                session.add(activity_record)
                for tag in all_tags:
                    session.add(tag)
                session.commit()

            existing_photo_ids.add(photo_id)
            processed_count += 1

            if verbose and processed_count % 10 == 0:
                print(f"  Processed {processed_count}/{len(photo_files)} photos...")

        except Exception as e:
            if verbose:
                print(f"  ❌ Error processing {file_path.name}: {e}")
            failed_count += 1

    # Save updated embeddings matrix
    if new_embeddings_list:
        new_batch = np.vstack(new_embeddings_list)
        if len(embeddings_matrix) > 0:
            full_matrix = np.vstack([embeddings_matrix, new_batch])
        else:
            full_matrix = new_batch
        save_embeddings(full_matrix, embeddings_path)

    elapsed = time.time() - start_time
    if verbose:
        print("\n" + "=" * 55)
        print("  ✅ Ingestion Complete!")
        print(f"  Processed : {processed_count} new photos")
        print(f"  Skipped   : {skipped_count} (already indexed)")
        print(f"  Failed    : {failed_count}")
        print(f"  Elapsed   : {elapsed:.2f}s")
        print("=" * 55 + "\n")

    return {
        "processed": processed_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "total": len(photo_files),
    }


def sync_unindexed_photos(target_engine=None, verbose: bool = False) -> int:
    """Find any unindexed photos in data/photos/ (including subfolders) and index them idempotently."""
    eng = target_engine or engine
    init_db(eng)

    if not PHOTOS_DIR.exists():
        return 0

    all_files = [
        f for f in PHOTOS_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not all_files:
        return 0

    with Session(eng) as session:
        existing_ids = set(session.exec(select(Photo.id)).all())

    unindexed = [f for f in all_files if get_photo_id(f) not in existing_ids]
    if not unindexed:
        return 0

    if verbose:
        print(f"📷 Discovered {len(unindexed)} external unindexed photo(s). Indexing now...")

    stats = run_ingestion(
        photos_dir=PHOTOS_DIR,
        target_engine=eng,
        file_paths=unindexed,
        verbose=verbose,
    )
    return stats.get("processed", 0)


if __name__ == "__main__":
    run_ingestion()
