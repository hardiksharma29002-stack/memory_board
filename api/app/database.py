"""Database engine and session management for SQLite."""

from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from .config import DB_PATH, DATA_DIR


def get_engine(db_path=None):
    """Create and return the SQLite engine."""
    target_path = db_path or DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{target_path}"
    return create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


engine = get_engine()


def init_db(target_engine=None) -> None:
    """Create all database tables."""
    from . import models  # Ensure all models are registered
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(target_engine or engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session
