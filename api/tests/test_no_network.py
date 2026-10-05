"""Privacy guarantee test: Fails if any outbound network call is made during processing."""

import socket
from pathlib import Path
from PIL import Image
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from api.app.ingest.pipeline import run_ingestion


def test_no_outbound_network_during_ingestion(temp_photos_dir, monkeypatch):
    """Ensure that the photo ingestion pipeline makes ZERO outbound network calls."""
    photos_dir = temp_photos_dir / "photos"
    photos_dir.mkdir()

    # Create dummy photo
    img_path = photos_dir / "private_photo.jpg"
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    img.save(img_path, format="JPEG")

    # Monkeypatch socket to raise an exception on any network attempt
    def blocked_connect(*args, **kwargs):
        raise RuntimeError("PRIVACY VIOLATION: Outbound network call attempted during local processing!")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    embeddings_file = temp_photos_dir / "embeddings.npy"

    # Should run and complete without triggering any network call
    result = run_ingestion(
        photos_dir=photos_dir,
        target_engine=test_engine,
        embeddings_path=embeddings_file,
        verbose=False,
    )

    assert result["processed"] == 1
    assert result["failed"] == 0
