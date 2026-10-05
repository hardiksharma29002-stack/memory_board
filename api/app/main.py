"""FastAPI main application entry point."""

import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import select, Session, func

from .config import CONFIG, DATA_DIR, PHOTOS_DIR, THUMBS_DIR
from .database import engine, init_db
from .models import Photo
from .routes.ingest import router as ingest_router
from .routes.photos import router as photos_router
from .routes.session import router as session_router
from .routes.activity import router as activity_router
from .routes.events import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories and database tables exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    try:
        from .ingest.pipeline import sync_unindexed_photos
        sync_unindexed_photos(verbose=False)
    except Exception:
        pass
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="Memory Board API",
    description="Backend service for Memory Board photo retrieval prototype",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import FileResponse, Response
from .routes.photos import get_photo_thumbnail, generate_svg_placeholder

DATA_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/thumbs/{filename}")
def serve_thumbnail_file(filename: str):
    """Serve thumbnail with high-performance caching, dynamic recovery, and zero broken images."""
    file_path = THUMBS_DIR / filename
    if file_path.exists() and file_path.stat().st_size > 0:
        return FileResponse(file_path, media_type="image/webp", headers={"Cache-Control": "public, max-age=86400, immutable"})

    # Extract photo_id and size
    m = re.match(r"^([a-f0-9]+)_(256|1024)\.webp$", filename, re.IGNORECASE)
    if m:
        photo_id, size_str = m.group(1), m.group(2)
        with Session(engine) as sess:
            return get_photo_thumbnail(photo_id=photo_id, size=int(size_str), db=sess)

    # Any other thumbnail name fallback
    svg = generate_svg_placeholder(photo_id=filename, label="Memory")
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/photos/{filename}")
def serve_photo_file(filename: str):
    """Serve full-resolution photo with fail-safe fallback."""
    file_path = PHOTOS_DIR / filename
    if file_path.exists() and file_path.stat().st_size > 0:
        return FileResponse(file_path, headers={"Cache-Control": "public, max-age=86400"})

    # Check case-insensitive match or search in photos dir
    for f in PHOTOS_DIR.iterdir():
        if f.name.lower() == filename.lower() and f.is_file():
            return FileResponse(f, headers={"Cache-Control": "public, max-age=86400"})

    svg = generate_svg_placeholder(photo_id=filename, label="Photo")
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


app.mount("/photos", StaticFiles(directory=str(PHOTOS_DIR)), name="photos")
app.mount("/thumbs", StaticFiles(directory=str(THUMBS_DIR)), name="thumbs")

app.include_router(ingest_router)
app.include_router(photos_router)
app.include_router(session_router)
app.include_router(activity_router)
app.include_router(events_router)


@app.get("/api/health")
def health_check():
    """Health check endpoint returning system status and photo index count."""
    photo_count = 0
    try:
        with Session(engine) as session:
            photo_count = session.exec(select(func.count(Photo.id))).one()
    except Exception:
        pass

    return {
        "status": "ok",
        "photos_indexed": photo_count,
        "config_loaded": True,
        "min_library_for_board": CONFIG.board.min_library_for_board,
    }
