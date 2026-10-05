"""Session REST API endpoints for Memory Board search flow."""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from ..database import get_session as get_db_session
from ..engine.session import (
    create_session,
    get_session,
    add_clue,
    remove_clue,
    rewind_session,
    complete_session,
    asdict,
)
from ..engine.cue_board import generate_cue_cards
from ..engine.groups import build_candidate_groups
from ..engine.questions import select_best_question
from ..engine.almost import pivot_almost
from ..engine.fallback import resolve_fallback
from ..vocab import CUE_LOOKUP, QUESTIONS, QUESTION_LOOKUP
from ..engine.next_wave import (
    check_hiding_places,
    match_paint_it_palette,
    segment_timeline_moments,
    get_who_was_there_options,
)
from ..engine.memory_ai import (
    parse_vague_memory_to_clues,
    generate_cognitive_cue_cards,
    generate_smart_cognitive_cards,
    generate_followup_memory_probes,
)

router = APIRouter(prefix="/api/session", tags=["session"])


class CreateSessionRequest(BaseModel):
    entry: str = "search_pill"
    initial_query: Optional[str] = None


class SelectCuesRequest(BaseModel):
    cue_ids: List[str]


class RemoveClueRequest(BaseModel):
    clue_id: str


class AnswerRequest(BaseModel):
    question_id: str
    option_id: str  # Can be "cant_recall"


class FoundRequest(BaseModel):
    photo_id: str


class AlmostRequest(BaseModel):
    photo_id: str
    difference_axis: str = "diff_look"


class SentenceRequest(BaseModel):
    blanks: dict[str, str]


class ParseMemoryRequest(BaseModel):
    query: str


class AddMemoryTextRequest(BaseModel):
    text: str


class SmartCardsRequest(BaseModel):
    query: Optional[str] = None
    selected_clues: Optional[List[str]] = None


@router.post("/parse-memory")
def parse_memory_endpoint(req: ParseMemoryRequest):
    """Parse user's incomplete memory input into 1-3 cognitive clues using Groq AI / heuristics."""
    clues = parse_vague_memory_to_clues(req.query)
    return {"query": req.query, "clues": clues}


@router.post("/smart-cards")
def get_smart_cards_endpoint(req: SmartCardsRequest):
    """Generate dynamic AI memory cue cards using Groq intelligence with safe rate limit caching."""
    cards = generate_smart_cognitive_cards(query=req.query or "", selected_clues=req.selected_clues or [])
    return {"cards": cards}


@router.post("")
def start_session(req: CreateSessionRequest, db: Session = Depends(get_db_session)):
    """Start a new search session, parse vague memory if provided, and generate cognitive memory cards."""
    sess = create_session(entry=req.entry, initial_query=req.initial_query, db=db)

    # 1. If user provided vague memory text at start, parse into 1-3 initial clues
    if req.initial_query and req.initial_query.strip():
        parsed = parse_vague_memory_to_clues(req.initial_query)
        for c in parsed:
            cid = c.get("cue_id")
            label = c.get("label", cid)
            add_clue(sess, clue_type="cue", label=label, value=cid, cue_id=cid, db=db)

    # 2. Non-pictorial cognitive memory trigger cards
    cognitive_cards = generate_cognitive_cue_cards([c.value for c in sess.clues])

    # 3. Traditional pictorial cards
    cards = generate_cue_cards(target_engine=db.bind)

    return {
        "session_id": sess.id,
        "step": sess.step,
        "initial_clues": [asdict(c) for c in sess.clues],
        "cognitive_cards": cognitive_cards,
        "cards": [
            {
                "cue_id": c.cue_id,
                "label": c.label,
                "group": c.group,
                "photo_count": c.photo_count,
                "preview_photo_ids": c.preview_photo_ids,
                "palette": c.palette,
            }
            for c in cards
        ],
    }


@router.post("/{session_id}/add-memory-text")
def add_memory_text(session_id: str, req: AddMemoryTextRequest, db: Session = Depends(get_db_session)):
    """User typed an additional memory fragment. Extract clues, update trail, and re-run macro albums."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    new_clues = parse_vague_memory_to_clues(req.text)
    for c in new_clues:
        cid = c.get("cue_id")
        label = c.get("label", cid)
        add_clue(sess, clue_type="cue", label=label, value=cid, cue_id=cid, db=db)

    sess.step = "groups"
    positive_cues = [c.value for c in sess.clues if c.type in ("cue", "answer", "sentence")]
    groups = build_candidate_groups(positive_cues=positive_cues, target_engine=db.bind)

    return {
        "session_id": sess.id,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
        "groups": groups,
    }


@router.get("/{session_id}")
def inspect_session(session_id: str):
    """Get active session details and clue trail."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": sess.id,
        "started_at": sess.started_at,
        "entry": sess.entry,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
        "history_depth": len(sess.history),
        "outcome": sess.outcome,
        "found_photo_id": sess.found_photo_id,
    }


@router.post("/{session_id}/cues")
def select_cues(session_id: str, req: SelectCuesRequest, db: Session = Depends(get_db_session)):
    """Add selected cue cards to the clue trail and compute candidate groups."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    for cid in req.cue_ids:
        cue = CUE_LOOKUP.get(cid)
        label = cue.label if cue else cid
        add_clue(sess, clue_type="cue", label=label, value=cid, cue_id=cid, db=db)

    sess.step = "groups"
    positive_cues = [c.value for c in sess.clues if c.type in ("cue", "answer")]
    groups = build_candidate_groups(positive_cues=positive_cues, target_engine=db.bind)

    return {
        "session_id": sess.id,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
        "groups": groups,
    }


@router.post("/{session_id}/clue/remove")
@router.post("/{session_id}/clues/remove")
def remove_session_clue(session_id: str, req: RemoveClueRequest):
    """Remove a clue from the clue trail."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    remove_clue(sess, req.clue_id)
    return {
        "session_id": sess.id,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
    }


@router.post("/{session_id}/rewind")
def rewind_last_action(session_id: str, db: Session = Depends(get_db_session)):
    """Rewind the session to the previous state."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    rewind_session(sess, db=db)
    return {
        "session_id": sess.id,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
    }


@router.post("/{session_id}/none")
def handle_none_of_these(session_id: str):
    """User tapped 'None of these' on Cue Board -> transition to question mode."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    # Record snapshot for rewind
    snapshot = {
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
        "question_count": sess.question_count,
    }
    sess.history.append(snapshot)

    sess.step = "question"
    # Select first unasked question from bank
    available_questions = [q for q in QUESTIONS if q.id not in sess.asked_question_ids]
    selected_question = available_questions[0] if available_questions else QUESTIONS[0]
    sess.asked_question_ids.append(selected_question.id)
    sess.question_count += 1

    return {
        "session_id": sess.id,
        "step": sess.step,
        "question": {
            "id": selected_question.id,
            "prompt": selected_question.prompt,
            "options": [
                {"id": opt.id, "label": opt.label, "cue_id": opt.cue_id}
                for opt in selected_question.options
            ],
        },
    }


@router.post("/{session_id}/answer")
def answer_question(session_id: str, req: AnswerRequest, db: Session = Depends(get_db_session)):
    """Record answer to a question and update clue trail."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    q = QUESTION_LOOKUP.get(req.question_id)
    if q and req.option_id != "cant_recall":
        # Find matching option
        matched_opt = next((o for o in q.options if o.id == req.option_id), None)
        if matched_opt:
            add_clue(
                sess,
                clue_type="answer",
                label=f"{q.prompt}: {matched_opt.label}",
                value=matched_opt.cue_id or req.option_id,
                cue_id=matched_opt.cue_id,
                db=db,
            )

    # After answer, either ask next question or build groups
    # Max questions: 3
    if sess.question_count >= 3:
        sess.step = "groups"
        positive_cues = [c.value for c in sess.clues if c.type in ("cue", "answer")]
        groups = build_candidate_groups(positive_cues=positive_cues, target_engine=db.bind)
        return {
            "session_id": sess.id,
            "step": "groups",
            "clues": [asdict(c) for c in sess.clues],
            "groups": groups,
        }

    # Ask next highest-gain question
    candidate_cues = [c.value for c in sess.clues if c.type in ("cue", "answer")]
    next_q = select_best_question(
        candidate_photo_ids=[],
        asked_question_ids=sess.asked_question_ids,
        target_engine=db.bind,
    )

    if next_q:
        sess.asked_question_ids.append(next_q.id)
        sess.question_count += 1
        return {
            "session_id": sess.id,
            "step": "question",
            "question": {
                "id": next_q.id,
                "prompt": next_q.prompt,
                "options": [
                    {"id": opt.id, "label": opt.label, "cue_id": opt.cue_id}
                    for opt in next_q.options
                ],
            },
            "clues": [asdict(c) for c in sess.clues],
        }

    # If no more questions, transition to groups
    sess.step = "groups"
    groups = build_candidate_groups(positive_cues=candidate_cues, target_engine=db.bind)
    return {
        "session_id": sess.id,
        "step": "groups",
        "clues": [asdict(c) for c in sess.clues],
        "groups": groups,
    }


@router.post("/{session_id}/almost")
def handle_almost(session_id: str, req: AlmostRequest, db: Session = Depends(get_db_session)):
    """User tapped 'Almost!' on a photo to pivot search."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    pivoted_photos = pivot_almost(
        photo_id=req.photo_id,
        difference_axis=req.difference_axis,
        target_engine=db.bind,
    )

    sess.step = "almost"
    return {
        "session_id": sess.id,
        "step": "almost",
        "anchor_photo_id": req.photo_id,
        "difference_axis": req.difference_axis,
        "photos": pivoted_photos,
    }


@router.post("/{session_id}/fallback")
@router.post("/{session_id}/not-here")
def handle_fallback(session_id: str):
    """Trigger graceful fallback ladder when no photos match, preserving full context."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    resolution = resolve_fallback(sess)
    sess.step = "fallback"

    # Context preservation: keep active clues & generate Groq AI follow-up probes
    clues_dicts = [asdict(c) for c in sess.clues]
    followup_data = generate_followup_memory_probes(active_clues=clues_dicts)

    return {
        "session_id": sess.id,
        "step": "fallback",
        "level": resolution.level,
        "message": resolution.message,
        "relaxed_clue_ids": resolution.relaxed_clue_ids,
        "suggested_question_id": resolution.suggested_question_id,
        "timeline_jump_date": resolution.timeline_jump_date,
        "clues": clues_dicts,
        "followup_probes": followup_data.get("probes", []),
        "preserved_context": followup_data.get("preserved_context", []),
        "cognitive_cards": generate_cognitive_cue_cards([c.value for c in sess.clues]),
    }


@router.post("/{session_id}/found")
def handle_photo_found(session_id: str, req: FoundRequest, db: Session = Depends(get_db_session)):
    """User confirmed target photo found!"""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    complete_session(sess, outcome="found", found_photo_id=req.photo_id, db=db)
    return {
        "session_id": sess.id,
        "status": "complete",
        "outcome": "found",
        "found_photo_id": req.photo_id,
    }


@router.post("/{session_id}/sentence")
def handle_sentence(session_id: str, req: SentenceRequest, db: Session = Depends(get_db_session)):
    """User filled in sentence blanks in Sentence Mode."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    for slot, val in req.blanks.items():
        if not val:
            continue
        cue = CUE_LOOKUP.get(val)
        label = cue.label if cue else f"{slot.capitalize()}: {val}"
        add_clue(sess, clue_type="sentence", label=label, value=val, cue_id=val if cue else None, db=db)

    sess.step = "groups"
    positive_cues = [c.value for c in sess.clues if c.type in ("cue", "answer", "sentence")]
    groups = build_candidate_groups(positive_cues=positive_cues, target_engine=db.bind)

    return {
        "session_id": sess.id,
        "step": sess.step,
        "clues": [asdict(c) for c in sess.clues],
        "groups": groups,
    }


class PaintItRequest(BaseModel):
    colors: List[str]  # e.g. ["#FF0000", "#00FF00"]
    day_night: Optional[str] = None  # "day" | "night"


@router.get("/features/hiding-places")
def get_hiding_places(db: Session = Depends(get_db_session)):
    """v1.1 Check simulated hiding places: trash, archived, locked, unbacked up."""
    return check_hiding_places(target_engine=db.bind)


@router.get("/features/moments")
def get_moments(db: Session = Depends(get_db_session)):
    """v1.1 Landmark moments segmentation across timeline."""
    moments = segment_timeline_moments(target_engine=db.bind)
    return {"moments": moments}


@router.post("/features/paint-it")
def paint_it_palette_search(req: PaintItRequest, db: Session = Depends(get_db_session)):
    """v1.1 Match photos by user-chosen color palette and day/night filter."""
    matched = match_paint_it_palette(
        target_hex_colors=req.colors,
        day_night=req.day_night,
        target_engine=db.bind,
    )
    return {"photos": matched, "matched_count": len(matched)}


@router.get("/{session_id}/who-was-there")
def who_was_there(session_id: str, db: Session = Depends(get_db_session)):
    """v1.1 Derive face count co-occurrence for candidates in current session."""
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    positive_cues = [c.value for c in sess.clues if c.type in ("cue", "answer", "sentence")]
    groups = build_candidate_groups(positive_cues=positive_cues, target_engine=db.bind)
    candidate_pids = [p["id"] for g in groups for p in g["photos"]]

    options = get_who_was_there_options(candidate_pids, target_engine=db.bind)
    return {"session_id": sess.id, "options": options}

