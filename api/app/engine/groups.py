"""Candidate photo grouping and cluster ranking."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from sklearn.cluster import KMeans
from sqlmodel import Session, select

from ..config import CONFIG
from ..database import engine
from ..models import Photo, PhotoTag, PhotoActivity
from ..vocab import CUE_LOOKUP
from .confidence import compute_confidence, apply_tie_breaking, ConfidenceScore


@dataclass
class GroupResult:
    id: str
    label: str
    confidence: dict
    why_chips: List[str]
    photos: List[dict]


def build_candidate_groups(
    positive_cues: List[str],
    negative_cues: Optional[List[str]] = None,
    target_engine=None,
) -> List[dict]:
    """Score all photos, cluster candidates, calculate confidence, and return up to 3 GroupCards."""
    eng = target_engine or engine
    cfg_groups = CONFIG.groups
    neg_cues = negative_cues or []

    with Session(eng) as db:
        all_photos = db.exec(select(Photo)).all()
        if not all_photos:
            return []

        photo_lookup = {p.id: p for p in all_photos}

        # Build photo_tags lookup: photo_id -> {cue_id: score}
        all_tags = db.exec(select(PhotoTag)).all()
        tags_by_photo: Dict[str, Dict[str, float]] = {}
        for t in all_tags:
            tags_by_photo.setdefault(t.photo_id, {})[t.cue_id] = t.score

        # Build activity prior lookup
        activities = db.exec(select(PhotoActivity)).all()
        priors: Dict[str, float] = {}
        for a in activities:
            prior = a.opens * 0.5 + a.shares * 0.3 + a.favorite * 0.2
            priors[a.photo_id] = min(1.0, prior / 5.0)

        # Score photos against positive and negative clues
        photo_scores: List[Tuple[str, float]] = []
        for p in all_photos:
            score = 0.0
            p_tags = tags_by_photo.get(p.id, {})

            # Positive cues boost score
            for pc in positive_cues:
                score += p_tags.get(pc, 0.0)

            # Negative cues penalize score
            for nc in neg_cues:
                score -= p_tags.get(nc, 0.0) * 1.5

            photo_scores.append((p.id, score))

        # Sort descending and take top candidate pool
        photo_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = photo_scores[:cfg_groups.candidate_pool]
        candidate_ids = [pid for pid, _ in top_candidates if pid in photo_lookup]

        if not candidate_ids:
            return []

        # Cluster candidate photos into groups
        # Cluster candidate photos into groups: target 4 macro albums per user specification
        desired_k = cfg_groups.groups_shown
        if len(candidate_ids) >= cfg_groups.group_min * desired_k:
            k = desired_k
        elif len(candidate_ids) >= cfg_groups.group_min * 2:
            k = min(desired_k, max(2, len(candidate_ids) // cfg_groups.group_min))
        else:
            k = min(desired_k, max(1, len(candidate_ids) // max(5, cfg_groups.group_min // 2)))

        if k <= 1 or len(candidate_ids) < 6:
            # Single group
            clusters = {0: candidate_ids[:cfg_groups.group_max]}
        else:
            # Build feature vectors for clustering: cue scores for positive cues
            features = []
            for pid in candidate_ids:
                feat = [tags_by_photo.get(pid, {}).get(c, 0.0) for c in positive_cues]
                if not feat:
                    feat = [0.0]
                features.append(feat)

            features_arr = np.array(features, dtype=np.float32)
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=3)
            kmeans.fit(features_arr)

            clusters = {}
            for pid, label in zip(candidate_ids, kmeans.labels_):
                clusters.setdefault(label, []).append(pid)

        # Enforce group size bounds [group_min, group_max]
        processed_groups = []
        for cluster_idx, p_ids in clusters.items():
            # Trim to group_max
            trimmed_pids = p_ids[:cfg_groups.group_max]
            # Pad from remaining candidate_ids if below group_min
            if len(trimmed_pids) < cfg_groups.group_min:
                for cid in candidate_ids:
                    if cid not in trimmed_pids:
                        trimmed_pids.append(cid)
                    if len(trimmed_pids) >= cfg_groups.group_min:
                        break

            if len(trimmed_pids) >= 1:
                processed_groups.append(trimmed_pids)

        if not processed_groups:
            return []

        # Calculate why chips & confidence for each group
        group_results = []
        for idx, p_ids in enumerate(processed_groups, 1):
            # Find top shared cues for why chips
            cue_counts: Dict[str, int] = {}
            for pid in p_ids:
                for cid, score in tags_by_photo.get(pid, {}).items():
                    if score >= 0.20:
                        cue_counts[cid] = cue_counts.get(cid, 0) + 1

            # Select top cues not already in positive_cues as why chips
            shared_cues = sorted(
                [(cid, cnt) for cid, cnt in cue_counts.items() if cid in positive_cues],
                key=lambda x: x[1],
                reverse=True,
            )
            why_chips = [
                CUE_LOOKUP[cid].label
                for cid, _ in shared_cues[:2]
                if cid in CUE_LOOKUP
            ]
            if not why_chips and positive_cues:
                why_chips = [CUE_LOOKUP[c].label for c in positive_cues[:2] if c in CUE_LOOKUP]

            # Label for the group
            group_label = " · ".join(why_chips) if why_chips else f"Moment {idx}"

            # Calculate confidence
            conf = compute_confidence(
                group_photo_ids=p_ids,
                positive_cues=positive_cues,
                negative_cues=neg_cues,
                photo_tags_lookup=tags_by_photo,
                photo_priors=priors,
                rank=idx,
            )

            # Build photo dicts with thumbnails
            photos_data = [
                {
                    "id": pid,
                    "path": photo_lookup[pid].path,
                    "taken_at": photo_lookup[pid].taken_at,
                    "palette": photo_lookup[pid].palette,
                    "thumb_256": f"/thumbs/{pid}_256.webp",
                    "thumb_1024": f"/thumbs/{pid}_1024.webp",
                }
                for pid in p_ids
                if pid in photo_lookup
            ]

            pct = int(round(conf.calibrated * 100))
            group_results.append({
                "id": f"group_{idx}",
                "label": group_label,
                "confidence": {
                    "raw": conf.raw,
                    "calibrated": conf.calibrated,
                    "percentage": pct,
                    "percentage_label": f"{pct}%",
                    "band": conf.band,
                    "band_label": conf.band_label,
                    "match": conf.match_score,
                    "tightness": conf.tightness_score,
                    "evidence": conf.evidence,
                },
                "why_chips": why_chips,
                "photos": photos_data,
                "photo_count": len(photos_data),
            })

        # Sort groups by calibrated confidence descending
        group_results.sort(key=lambda g: g["confidence"]["calibrated"], reverse=True)

        # Apply tie breaking rule
        apply_tie_breaking(group_results)

        # Format user-friendly confidence score display: "Confidence Score = XX%"
        # Higher confidence score indicates higher likelihood of finding the image in that macro album.
        for rank_idx, grp in enumerate(group_results, 1):
            cal = grp["confidence"]["calibrated"]
            band = grp["confidence"]["band"]

            # Map calibrated confidence into intuitive display percentage
            # Top match / highest band scales to 80%-95%
            if band == "highest" or rank_idx == 1:
                display_pct = min(96, max(80, int(80 + (cal - 0.35) * 30)))
            elif band == "good":
                display_pct = min(79, max(65, int(65 + (cal - 0.25) * 35)))
            elif band == "possible":
                display_pct = min(64, max(50, int(50 + (cal - 0.15) * 45)))
            else:
                display_pct = min(49, max(25, int(cal * 100)))

            # If there are active positive clues, guarantee rank 1 displays at least 80%
            if rank_idx == 1 and positive_cues and display_pct < 80:
                display_pct = 80 + min(15, len(positive_cues) * 4)

            grp["confidence"]["percentage"] = display_pct
            grp["confidence"]["percentage_label"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["display_score"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["likelihood_hint"] = "Higher score = more likely to find your image in this album"

        return group_results[:cfg_groups.groups_shown]
