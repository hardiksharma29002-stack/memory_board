"""Zero-shot cue tag scoring per photo using CLIP embeddings and rule-based priors."""

from typing import Dict, List, Tuple
import numpy as np

from ..vocab import CUES, CUES_BY_GROUP, Cue
from ..models import PhotoTag


def compute_rule_based_tags(photo_id: str, face_count: int) -> List[PhotoTag]:
    """Compute deterministic tags for rule-based cues (e.g. people count)."""
    tags = []

    # people_solo
    tags.append(PhotoTag(
        photo_id=photo_id,
        cue_id="people_solo",
        score=1.0 if face_count == 1 else 0.0,
    ))

    # people_pair
    tags.append(PhotoTag(
        photo_id=photo_id,
        cue_id="people_pair",
        score=1.0 if face_count == 2 else 0.0,
    ))

    # people_group
    tags.append(PhotoTag(
        photo_id=photo_id,
        cue_id="people_group",
        score=1.0 if 3 <= face_count <= 5 else 0.0,
    ))

    # people_crowd
    tags.append(PhotoTag(
        photo_id=photo_id,
        cue_id="people_crowd",
        score=1.0 if face_count >= 6 else 0.0,
    ))

    return tags


def compute_clip_tags(
    photo_id: str,
    image_embedding: np.ndarray,
    cue_text_embeddings: Dict[str, np.ndarray],
) -> List[PhotoTag]:
    """Compute zero-shot similarity scores between photo embedding and cue text embeddings."""
    tags = []

    for group_name, group_cues in CUES_BY_GROUP.items():
        if group_name == "people":
            continue  # People cues are rule-based from face count

        group_similarities = []
        for cue in group_cues:
            if cue.id in cue_text_embeddings:
                text_emb = cue_text_embeddings[cue.id]
                # Cosine similarity (both are L2-normalized)
                sim = float(np.dot(image_embedding, text_emb))
                group_similarities.append((cue.id, sim))

        if not group_similarities:
            continue

        # Softmax or temperature-scaled normalization within group
        sims = np.array([s for _, s in group_similarities])
        temperature = 0.07  # standard CLIP temperature
        exp_sims = np.exp((sims - np.max(sims)) / temperature)
        probs = exp_sims / np.sum(exp_sims)

        for (cue_id, _), prob in zip(group_similarities, probs):
            tags.append(PhotoTag(
                photo_id=photo_id,
                cue_id=cue_id,
                score=round(float(prob), 4),
            ))

    return tags
