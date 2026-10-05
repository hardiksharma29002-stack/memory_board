"""Tests for ingestion pipeline components."""

import numpy as np
from PIL import Image
from pathlib import Path
from sqlmodel import Session, select, create_engine
from sqlmodel.pool import StaticPool

from api.app.ingest.exif import extract_exif
from api.app.ingest.thumbnails import generate_thumbnails
from api.app.ingest.palette import extract_palette
from api.app.ingest.sharpness import compute_sharpness_and_brightness
from api.app.ingest.source import infer_source
from api.app.ingest.pipeline import run_ingestion
from api.app.models import Photo, PhotoTag


def create_dummy_image(path: Path, width=400, height=300, color=(255, 100, 50)):
    """Helper to generate a test image."""
    img = Image.new("RGB", (width, height), color=color)
    img.save(path, format="JPEG")
    return path


def test_thumbnails_generation(temp_photos_dir):
    """Verify 256px and 1024px WebP thumbnails are generated correctly."""
    img_path = create_dummy_image(temp_photos_dir / "sample.jpg", width=1200, height=800)
    thumbs_dir = temp_photos_dir / "thumbs"
    thumbs = generate_thumbnails(img_path, "sample_1", output_dir=thumbs_dir)

    assert thumbs["thumb_256"].exists()
    assert thumbs["thumb_1024"].exists()

    with Image.open(thumbs["thumb_256"]) as t256:
        assert max(t256.size) <= 256
        assert t256.format == "WEBP"

    with Image.open(thumbs["thumb_1024"]) as t1024:
        assert max(t1024.size) <= 1024
        assert t1024.format == "WEBP"


def test_palette_extraction(temp_photos_dir):
    """Verify that palette returns 3 valid hex colors."""
    img_path = create_dummy_image(temp_photos_dir / "palette_test.jpg", color=(200, 50, 50))
    palette = extract_palette(img_path, k=3)
    assert len(palette) == 3
    for hex_color in palette:
        assert hex_color.startswith("#")
        assert len(hex_color) == 7


def test_sharpness_and_brightness(temp_photos_dir):
    """Verify sharpness and brightness produce valid values."""
    img_path = create_dummy_image(temp_photos_dir / "sharp.jpg", color=(128, 128, 128))
    sharpness, brightness = compute_sharpness_and_brightness(img_path)
    assert sharpness >= 0.0
    assert 0.0 <= brightness <= 1.0


def test_exif_fallback_when_no_exif(temp_photos_dir):
    """Verify hour_bucket fallback when EXIF data is absent."""
    img_path = create_dummy_image(temp_photos_dir / "no_exif.jpg")
    exif_info = extract_exif(img_path, brightness=0.1)  # Dark image
    assert exif_info["hour_bucket"] == 22  # Inferred night

    exif_info_day = extract_exif(img_path, brightness=0.7)  # Bright image
    assert exif_info_day["hour_bucket"] == 14  # Inferred afternoon


def test_source_inference():
    """Verify source rules identify camera, screenshot, and received media."""
    assert infer_source(Path("Screenshot_2026-10-05.png")) == "screenshot"
    assert infer_source(Path("IMG-20261005-WA0012.jpg")) == "received"
    assert infer_source(Path("Instagram_photo_post.jpg")) == "saved"
    assert infer_source(Path("IMG_20261005_123456.jpg")) == "camera"


def test_pipeline_idempotency(temp_photos_dir):
    """Verify pipeline processes photos and is idempotent on rerun."""
    photos_dir = temp_photos_dir / "photos"
    photos_dir.mkdir()
    create_dummy_image(photos_dir / "photo1.jpg")
    create_dummy_image(photos_dir / "photo2.jpg")

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    embeddings_file = temp_photos_dir / "embeddings.npy"

    # First run
    res1 = run_ingestion(
        photos_dir=photos_dir,
        target_engine=test_engine,
        embeddings_path=embeddings_file,
        verbose=False,
    )
    assert res1["processed"] == 2
    assert res1["skipped"] == 0

    with Session(test_engine) as session:
        photos = session.exec(select(Photo)).all()
        assert len(photos) == 2
        tags = session.exec(select(PhotoTag)).all()
        assert len(tags) > 0

    # Second run should skip all existing
    res2 = run_ingestion(
        photos_dir=photos_dir,
        target_engine=test_engine,
        embeddings_path=embeddings_file,
        verbose=False,
    )
    assert res2["processed"] == 0
    assert res2["skipped"] == 2
