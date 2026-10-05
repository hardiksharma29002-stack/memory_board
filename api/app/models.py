"""SQLModel database models for Memory Board."""

from typing import Optional
from sqlmodel import Field, SQLModel


class Photo(SQLModel, table=True):
    __tablename__ = "photos"

    id: str = Field(primary_key=True)
    path: str
    taken_at: Optional[str] = None
    hour_bucket: Optional[int] = None
    width: int = 0
    height: int = 0
    source: str = "camera"
    face_count: int = 0
    sharpness: float = 0.0
    brightness: float = 0.0
    palette: str = "[]"  # JSON list of 3 hex strings
    embedding_idx: Optional[int] = None
    in_trash: int = 0
    archived: int = 0
    locked: int = 0
    backed_up: int = 1


class PhotoTag(SQLModel, table=True):
    __tablename__ = "photo_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    photo_id: str = Field(foreign_key="photos.id", index=True)
    cue_id: str = Field(index=True)
    score: float = 0.0


class PhotoActivity(SQLModel, table=True):
    __tablename__ = "photo_activity"

    photo_id: str = Field(primary_key=True, foreign_key="photos.id")
    opens: int = 0
    shares: int = 0
    favorite: int = 0
    last_opened_at: Optional[str] = None


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    started_at: str
    ended_at: Optional[str] = None
    entry: str = "manual"  # search_pill, nudge, manual
    initial_query: Optional[str] = None
    outcome: Optional[str] = None  # found, abandoned, almost
    found_photo_id: Optional[str] = None


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[str] = Field(default=None, foreign_key="sessions.id", index=True)
    name: str
    ts: str
    payload: str = "{}"  # JSON string
