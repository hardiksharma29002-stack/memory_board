"""Thumbnail generation in 256px and 1024px WebP format."""

from pathlib import Path
from PIL import Image, ImageOps
from ..config import THUMBS_DIR


def generate_thumbnails(image_path: Path, photo_id: str, output_dir: Path = THUMBS_DIR) -> dict[str, Path]:
    """Generate 256px and 1024px WebP thumbnails preserving aspect ratio."""
    output_dir.mkdir(parents=True, exist_ok=True)
    thumb_256_path = output_dir / f"{photo_id}_256.webp"
    thumb_1024_path = output_dir / f"{photo_id}_1024.webp"

    # If both already exist, skip (idempotent)
    if thumb_256_path.exists() and thumb_1024_path.exists():
        return {"thumb_256": thumb_256_path, "thumb_1024": thumb_1024_path}

    with Image.open(image_path) as img:
        # Transpose image according to EXIF orientation tag if present
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # 1024px preview
        if not thumb_1024_path.exists():
            img_1024 = img.copy()
            img_1024.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            img_1024.save(thumb_1024_path, format="WEBP", quality=85)

        # 256px grid thumbnail
        if not thumb_256_path.exists():
            img_256 = img.copy()
            img_256.thumbnail((256, 256), Image.Resampling.LANCZOS)
            img_256.save(thumb_256_path, format="WEBP", quality=80)

    return {"thumb_256": thumb_256_path, "thumb_1024": thumb_1024_path}
