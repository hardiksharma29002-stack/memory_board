"""FastAPI main application entry point."""

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

# Mount static file directories for photos and thumbnails
DATA_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

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
