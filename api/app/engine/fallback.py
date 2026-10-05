"""No-dead-end fallback ladder when zero photos match search criteria."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .session import SearchSession, ClueRecord


@dataclass
class FallbackResolution:
    level: int           # 1 = relax clues, 2 = clarifying question, 3 = timeline jump
    message: str
    relaxed_clue_ids: List[str]
    suggested_question_id: Optional[str] = None
    timeline_jump_date: Optional[str] = None


def resolve_fallback(session: SearchSession) -> FallbackResolution:
    """Determine graceful recovery path when photo candidate set drops to zero."""
    if len(session.clues) > 1:
        # Step 1: Relax lowest weight clue or most recently added clue
        sorted_clues = sorted(session.clues, key=lambda c: (c.weight, c.step_index))
        weakest = sorted_clues[0]

        return FallbackResolution(
            level=1,
            message=f"No photos matched all criteria. We relaxed '{weakest.label}' to broaden your search.",
            relaxed_clue_ids=[weakest.id],
        )

    elif len(session.clues) == 1:
        # Step 2: Propose a clarifying question
        return FallbackResolution(
            level=2,
            message="We couldn't find a direct match. Answer a quick question to help narrow down:",
            relaxed_clue_ids=[],
            suggested_question_id="q_time",
        )

    else:
        # Step 3: Jump to recent timeline
        return FallbackResolution(
            level=3,
            message="Showing recent moments from your timeline.",
            relaxed_clue_ids=[],
            timeline_jump_date="recent",
        )
