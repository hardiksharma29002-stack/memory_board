"""Ingestion API route."""

from fastapi import APIRouter, BackgroundTasks
from ..ingest.pipeline import run_ingestion

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/run")
def trigger_ingest(background_tasks: BackgroundTasks):
    """Trigger background photo ingestion pipeline."""
    background_tasks.add_task(run_ingestion)
    return {"status": "started", "message": "Photo ingestion started in background"}
