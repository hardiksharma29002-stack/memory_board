"""Pytest fixtures for Memory Board tests."""

import os
import pytest
from pathlib import Path
import tempfile

os.environ["MEMORY_BOARD_TEST_MODE"] = "1"

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from api.app.main import app
from api.app.database import get_session
import api.app.models  # Register models


@pytest.fixture(name="session")
def session_fixture():
    """In-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """TestClient wired to the in-memory SQLite database."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="temp_photos_dir")
def temp_photos_dir_fixture():
    """Temporary directory for photo test fixtures."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
