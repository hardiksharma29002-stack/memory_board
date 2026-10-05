"""Telemetry REST API endpoint for recording event logs locally."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..database import get_session
from ..models import Event

router = APIRouter(prefix="/api/events", tags=["events"])


class EventPayload(BaseModel):
    name: str
    session_id: Optional[str] = None
    ts: Optional[str] = None
    payload: Optional[Union[Dict[str, Any], str]] = None


class BatchEventsRequest(BaseModel):
    events: List[EventPayload]


@router.post("")
def record_events(
    body: Union[BatchEventsRequest, List[EventPayload], EventPayload],
    db: Session = Depends(get_session),
):
    """Batch-record telemetry events locally to SQLite for evaluation and metrics."""
    if isinstance(body, BatchEventsRequest):
        event_list = body.events
    elif isinstance(body, list):
        event_list = body
    else:
        event_list = [body]

    now_iso = datetime.now(timezone.utc).isoformat()
    created_count = 0

    for item in event_list:
        ts = item.ts or now_iso
        if isinstance(item.payload, (dict, list)):
            payload_str = json.dumps(item.payload)
        elif item.payload is None:
            payload_str = "{}"
        else:
            payload_str = str(item.payload)

        event_record = Event(
            session_id=item.session_id,
            name=item.name,
            ts=ts,
            payload=payload_str,
        )
        db.add(event_record)
        created_count += 1

    db.commit()
    return {"status": "ok", "recorded": created_count}
