"""Information-gain question selector using Shannon entropy."""

import math
from typing import Dict, List, Optional, Set
from sqlmodel import Session, select

from ..config import CONFIG
from ..database import engine
from ..models import Photo, PhotoTag
from ..vocab import QUESTIONS, Question, QuestionOption


def compute_entropy(probabilities: List[float]) -> float:
    """Compute Shannon entropy H = -Σ p * log2(p)."""
    entropy = 0.0
    for p in probabilities:
        if p > 0.0:
            entropy -= p * math.log2(p)
    return entropy


def select_best_question(
    candidate_photo_ids: List[str],
    asked_question_ids: List[str],
    target_engine=None,
) -> Optional[Question]:
    """Select the question from the question bank with the highest information gain."""
    eng = target_engine or engine
    cfg_q = CONFIG.questions
    n_candidates = len(candidate_photo_ids)

    if n_candidates == 0:
        # Fallback to first unasked question
        for q in QUESTIONS:
            if q.id not in asked_question_ids:
                return q
        return None

    # Load tags for candidates
    with Session(eng) as db:
        tags = db.exec(
            select(PhotoTag)
            .where(PhotoTag.photo_id.in_(candidate_photo_ids))
        ).all()

        photo_cues: Dict[str, Set[str]] = {}
        for t in tags:
            if t.score >= 0.20:
                photo_cues.setdefault(t.photo_id, set()).add(t.cue_id)

    best_question = None
    best_gain = -1.0

    for question in QUESTIONS:
        if question.id in asked_question_ids:
            continue

        # Calculate probability distribution over options for this question
        option_counts = []
        for opt in question.options:
            if opt.cue_id:
                count = sum(
                    1 for pid in candidate_photo_ids
                    if opt.cue_id in photo_cues.get(pid, set())
                )
            else:
                count = n_candidates // len(question.options)  # Uniform estimate for unmodeled
            option_counts.append(count)

        total_matches = sum(option_counts)
        if total_matches == 0:
            probs = [1.0 / len(question.options)] * len(question.options)
        else:
            probs = [c / total_matches for c in option_counts]

        entropy = compute_entropy(probs)

        # Check threshold
        if entropy > best_gain:
            best_gain = entropy
            best_question = question

    # If best gain meets min_gain_bits or no other question available
    if best_question and (best_gain >= cfg_q.min_gain_bits or not asked_question_ids):
        return best_question

    # Return next unasked question as fallback
    for q in QUESTIONS:
        if q.id not in asked_question_ids:
            return q

    return None
