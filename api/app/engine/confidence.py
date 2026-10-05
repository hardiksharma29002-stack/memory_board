"""Confidence engine implementing honest, formula-driven probability bands."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import numpy as np

from ..config import CONFIG


@dataclass
class ConfidenceScore:
    raw: float
    calibrated: float
    band: str           # highest | good | possible | unsure
    band_label: str     # Highest chance | Good chance | Possible | Not sure yet
    match_score: float
    exclusion_score: float
    tightness_score: float
    prior_score: float
    evidence: float


def compute_confidence(
    group_photo_ids: List[str],
    positive_cues: List[str],       # P = selected cues
    negative_cues: List[str],       # N = excluded/rejected cues
    photo_tags_lookup: Dict[str, Dict[str, float]],  # photo_id -> {cue_id: score}
    photo_embeddings: Optional[Dict[str, np.ndarray]] = None,
    photo_priors: Optional[Dict[str, float]] = None,
    rank: int = 1,
) -> ConfidenceScore:
    """Calculate confidence score for a candidate photo group based on the formula."""
    cfg = CONFIG.confidence
    n_group = len(group_photo_ids)
    if n_group == 0 or not positive_cues:
        return ConfidenceScore(
            raw=0.0,
            calibrated=0.0,
            band="unsure",
            band_label="Not sure yet",
            match_score=0.0,
            exclusion_score=0.0,
            tightness_score=0.0,
            prior_score=0.0,
            evidence=0.0,
        )

    # 1. Match score: Σ w_c * frac(G, c) / Σ w_c
    match_terms = []
    for c in positive_cues:
        matching_photos = sum(
            1 for pid in group_photo_ids
            if photo_tags_lookup.get(pid, {}).get(c, 0.0) >= 0.20
        )
        frac = matching_photos / n_group
        match_terms.append(frac)
    match_score = float(np.mean(match_terms)) if match_terms else 0.0

    # 2. Exclusion score: Σ w_n * frac(G, n) / Σ w_n
    if negative_cues:
        excl_terms = []
        for n in negative_cues:
            matching_photos = sum(
                1 for pid in group_photo_ids
                if photo_tags_lookup.get(pid, {}).get(n, 0.0) >= 0.20
            )
            frac = matching_photos / n_group
            excl_terms.append(frac)
        exclusion_score = float(np.mean(excl_terms))
    else:
        exclusion_score = 0.0

    # 3. Tightness (cluster cohesion)
    tightness_score = 0.5  # Neutral default
    if photo_embeddings and len(group_photo_ids) >= 2:
        embs = [
            photo_embeddings[pid]
            for pid in group_photo_ids
            if pid in photo_embeddings
        ]
        if len(embs) >= 2:
            matrix = np.array(embs)
            # Dot product similarity matrix
            sim_matrix = np.dot(matrix, matrix.T)
            # Average upper triangle
            n = len(embs)
            triu_indices = np.triu_indices(n, k=1)
            mean_sim = float(np.mean(sim_matrix[triu_indices]))
            tightness_score = float(np.clip((mean_sim - 0.5) / 0.4, 0.0, 1.0))

    # 4. Behaviour Prior (opens, shares, favorites)
    if photo_priors:
        prior_vals = [photo_priors.get(pid, 0.0) for pid in group_photo_ids]
        prior_score = float(np.mean(prior_vals)) if prior_vals else 0.1
    else:
        prior_score = 0.1

    # 5. Evidence factor: min(1.0, |P| / evidence_clues_for_full)
    evidence = float(min(1.0, len(positive_cues) / cfg.evidence_clues_for_full))

    # Raw confidence formula
    raw = (
        cfg.w_match * match_score
        - cfg.w_exclusion * exclusion_score
        + cfg.w_tight * tightness_score
        + cfg.w_prior * prior_score
    )
    raw = float(np.clip(raw, 0.0, 1.0))

    # Discounted by evidence factor: raw * (0.6 + 0.4 * evidence)
    conf = float(raw * (0.6 + 0.4 * evidence))
    conf = round(conf, 4)

    # Band mapping
    bands = cfg.bands
    if conf >= bands.highest and rank == 1:
        band = "highest"
        band_label = "Highest chance"
    elif conf >= bands.good:
        band = "good"
        band_label = "Good chance"
    elif conf >= bands.possible:
        band = "possible"
        band_label = "Possible"
    else:
        band = "unsure"
        band_label = "Not sure yet"

    return ConfidenceScore(
        raw=round(raw, 4),
        calibrated=conf,
        band=band,
        band_label=band_label,
        match_score=round(match_score, 4),
        exclusion_score=round(exclusion_score, 4),
        tightness_score=round(tightness_score, 4),
        prior_score=round(prior_score, 4),
        evidence=round(evidence, 4),
    )


def apply_tie_breaking(groups_with_conf: List[dict]) -> None:
    """Apply the tie rule: if top two groups are within tie_margin (0.05), both get 'good' band."""
    cfg = CONFIG.confidence
    if len(groups_with_conf) >= 2:
        top1 = groups_with_conf[0]
        top2 = groups_with_conf[1]
        diff = abs(top1["confidence"]["calibrated"] - top2["confidence"]["calibrated"])
        if diff <= cfg.tie_margin:
            if top1["confidence"]["band"] == "highest":
                top1["confidence"]["band"] = "good"
                top1["confidence"]["band_label"] = "Good chance"
            if top2["confidence"]["band"] in ("highest", "possible"):
                top2["confidence"]["band"] = "good"
                top2["confidence"]["band_label"] = "Good chance"
