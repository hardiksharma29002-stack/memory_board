"""Session state machine and clue trail management."""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlmodel import Session as DbSession, select

from ..config import CONFIG
from ..database import engine
from ..models import Session as DbSessionModel, Event as DbEventModel


@dataclass
class ClueRecord:
    id: str
    type: str  # cue | answer | source | almost | text
    label: str
    value: str
    cue_id: Optional[str] = None
    weight: float = 1.0
    step_index: int = 0


@dataclass
class SearchSession:
    id: str
    started_at: str
    entry: str
    step: str = "cue_board"
    clues: List[ClueRecord] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)  # Snapshots for rewind
    initial_query: Optional[str] = None
    outcome: Optional[str] = None
    found_photo_id: Optional[str] = None
    question_count: int = 0
    asked_question_ids: List[str] = field(default_factory=list)


# In-memory store for active interactive sessions
_ACTIVE_SESSIONS: Dict[str, SearchSession] = {}


def create_session(
    entry: str = "search_pill",
    initial_query: Optional[str] = None,
    db: Optional[DbSession] = None,
) -> SearchSession:
    """Create a new search session and persist initial record."""
    session_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    sess = SearchSession(
        id=session_id,
        started_at=now_iso,
        entry=entry,
        initial_query=initial_query,
        step="cue_board",
    )

    def _persist(database: DbSession):
        db_record = DbSessionModel(
            id=session_id,
            started_at=now_iso,
            entry=entry,
            initial_query=initial_query,
        )
        database.add(db_record)

        event = DbEventModel(
            session_id=session_id,
            name="session_created",
            ts=now_iso,
            payload=json.dumps({"entry": entry, "query": initial_query}),
        )
        database.add(event)
        database.commit()

    if db is not None:
        _persist(db)
    else:
        with DbSession(engine) as local_db:
            _persist(local_db)

    _ACTIVE_SESSIONS[session_id] = sess
    return sess


def get_session(session_id: str) -> Optional[SearchSession]:
    """Retrieve an existing search session."""
    return _ACTIVE_SESSIONS.get(session_id)


def add_clue(
    session: SearchSession,
    clue_type: str,
    label: str,
    value: str,
    cue_id: Optional[str] = None,
    db: Optional[DbSession] = None,
) -> SearchSession:
    """Add a clue to the session and record a history snapshot for rewind."""
    # Deduplicate: if clue with same value, cue_id, or identical label already exists, skip
    val_norm = str(value).strip().lower()
    lbl_norm = str(label).strip().lower()
    for existing in session.clues:
        if (
            str(existing.value).strip().lower() == val_norm
            or (cue_id and existing.cue_id == cue_id)
            or str(existing.label).strip().lower() == lbl_norm
        ):
            return session

    # Save snapshot for rewind
    snapshot = {
        "step": session.step,
        "clues": [asdict(c) for c in session.clues],
        "question_count": session.question_count,
    }
    session.history.append(snapshot)

    # Determine weight
    weight_map = {
        "cue": CONFIG.clue_weights.cue,
        "answer": CONFIG.clue_weights.answer,
        "source": CONFIG.clue_weights.source,
        "sentence": CONFIG.clue_weights.sentence,
        "almost": CONFIG.clue_weights.almost,
    }
    weight = weight_map.get(clue_type, 1.0)

    clue = ClueRecord(
        id=f"clue_{len(session.clues) + 1}",
        type=clue_type,
        label=label,
        value=value,
        cue_id=cue_id,
        weight=weight,
        step_index=len(session.history),
    )
    session.clues.append(clue)

    # Log event
    now_iso = datetime.now(timezone.utc).isoformat()
    def _log(database: DbSession):
        event = DbEventModel(
            session_id=session.id,
            name="clue_added",
            ts=now_iso,
            payload=json.dumps(asdict(clue)),
        )
        database.add(event)
        database.commit()

    if db is not None:
        _log(db)
    else:
        with DbSession(engine) as local_db:
            _log(local_db)

    return session


def remove_clue(session: SearchSession, clue_id: str) -> SearchSession:
    """Remove a specific clue by ID."""
    session.clues = [c for c in session.clues if c.id != clue_id]
    return session


def rewind_session(session: SearchSession, db: Optional[DbSession] = None) -> SearchSession:
    """Rewind session back to the previous snapshot."""
    if not session.history:
        return session

    last_state = session.history.pop()
    session.step = last_state["step"]
    session.question_count = last_state["question_count"]
    session.clues = [ClueRecord(**c) for c in last_state["clues"]]

    # Log event
    now_iso = datetime.now(timezone.utc).isoformat()
    def _log(database: DbSession):
        event = DbEventModel(
            session_id=session.id,
            name="session_rewound",
            ts=now_iso,
            payload=json.dumps({"clues_remaining": len(session.clues)}),
        )
        database.add(event)
        database.commit()

    if db is not None:
        _log(db)
    else:
        with DbSession(engine) as local_db:
            _log(local_db)

    return session


def complete_session(
    session: SearchSession,
    outcome: str,
    found_photo_id: Optional[str] = None,
    db: Optional[DbSession] = None,
) -> None:
    """Mark session as complete (found | almost | abandoned)."""
    session.outcome = outcome
    session.found_photo_id = found_photo_id
    now_iso = datetime.now(timezone.utc).isoformat()

    def _persist(database: DbSession):
        db_sess = database.get(DbSessionModel, session.id)
        if db_sess:
            db_sess.ended_at = now_iso
            db_sess.outcome = outcome
            db_sess.found_photo_id = found_photo_id
            database.add(db_sess)

        event = DbEventModel(
            session_id=session.id,
            name=f"session_{outcome}",
            ts=now_iso,
            payload=json.dumps({"found_photo_id": found_photo_id}),
        )
        database.add(event)
        database.commit()

    if db is not None:
        _persist(db)
    else:
        with DbSession(engine) as local_db:
            _persist(local_db)
