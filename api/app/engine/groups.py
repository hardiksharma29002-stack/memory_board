"""Candidate photo grouping and cluster ranking."""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from sklearn.cluster import KMeans
from sqlmodel import Session, select

from ..config import CONFIG, EMBEDDINGS_PATH
from ..database import engine
from ..models import Photo, PhotoTag, PhotoActivity
from ..vocab import CUE_LOOKUP, CUES
from .confidence import compute_confidence, apply_tie_breaking, ConfidenceScore


@dataclass
class GroupResult:
    id: str
    label: str
    confidence: dict
    why_chips: List[str]
    photos: List[dict]


def build_candidate_groups(
    positive_cues: Optional[List[str]] = None,
    negative_cues: Optional[List[str]] = None,
    target_engine=None,
    query: Optional[str] = None,
) -> List[dict]:
    """Score all photos, cluster candidates, calculate confidence, and return up to 4 distinct Macro Albums."""
    eng = target_engine or engine
    cfg_groups = CONFIG.groups
    pos_cues = list(dict.fromkeys(positive_cues or []))
    neg_cues = list(dict.fromkeys(negative_cues or []))

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

        # Load CLIP embeddings if query provided
        embeddings_matrix = None
        query_emb = None
        if query and query.strip():
            if EMBEDDINGS_PATH.exists():
                try:
                    embeddings_matrix = np.load(EMBEDDINGS_PATH)
                except Exception:
                    embeddings_matrix = None
            try:
                from ..ingest.embeddings import compute_text_embedding
                query_emb = compute_text_embedding(query.strip())
            except Exception:
                query_emb = None

        # Score photos against positive cues, negative cues, and query embedding
        photo_scores: List[Tuple[str, float]] = []
        for p in all_photos:
            p_tags = tags_by_photo.get(p.id, {})
            score = 0.0

            # 1. Cue-based matching
            cue_score = 0.0
            if pos_cues:
                for pc in pos_cues:
                    cue_score += p_tags.get(pc, 0.0)
                cue_score = cue_score / len(pos_cues)

            for nc in neg_cues:
                cue_score -= p_tags.get(nc, 0.0) * 1.5

            # 2. Query embedding semantic matching (preserves original context)
            q_score = 0.0
            if query_emb is not None and embeddings_matrix is not None:
                if p.embedding_idx is not None and 0 <= p.embedding_idx < len(embeddings_matrix):
                    q_score = float(np.dot(embeddings_matrix[p.embedding_idx], query_emb))

            # Combine scores preserving both query context and refined cues
            if pos_cues and (query_emb is not None):
                score = 0.45 * q_score + 0.55 * cue_score
            elif pos_cues:
                score = cue_score
            elif query_emb is not None:
                score = q_score
            else:
                score = priors.get(p.id, 0.0) * 0.3 + (p.sharpness or 0.0) * 0.1

            photo_scores.append((p.id, score))

        # Sort descending and take top candidate pool
        photo_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = photo_scores[:cfg_groups.candidate_pool]
        candidate_ids = [pid for pid, _ in top_candidates if pid in photo_lookup]

        if not candidate_ids:
            return []

        # Cluster candidate photos into groups using multi-dimensional context
        desired_k = cfg_groups.groups_shown
        k = max(1, min(desired_k, len(candidate_ids)))

        clusters: Dict[int, List[str]] = {}
        if k <= 1 or len(candidate_ids) < 4:
            clusters = {0: candidate_ids[:cfg_groups.group_max]}
        else:
            try:
                # Use all primary cues + visual metadata for multi-dimensional orthogonal clustering
                all_cue_ids = [c.id for c in CUES]
                features = []
                for pid in candidate_ids:
                    p_tags = tags_by_photo.get(pid, {})
                    feat = [p_tags.get(cid, 0.0) for cid in all_cue_ids]
                    p_obj = photo_lookup.get(pid)
                    if p_obj:
                        feat.append(float(p_obj.brightness or 0.5))
                        feat.append(float(p_obj.face_count or 0) * 0.2)
                    features.append(feat)

                features_arr = np.array(features, dtype=np.float32)
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=3)
                kmeans.fit(features_arr)

                for pid, label in zip(candidate_ids, kmeans.labels_):
                    clusters.setdefault(int(label), []).append(pid)
            except Exception:
                # Fallback round-robin if KMeans fails
                clusters = {}
                for idx, pid in enumerate(candidate_ids):
                    clusters.setdefault(idx % k, []).append(pid)

        # Burst / duplicate photo diversification
        processed_groups = []
        for cluster_idx, p_ids in clusters.items():
            # Group burst photos (within 8 seconds of each other or identical tags)
            distinct_pids = []
            burst_extras = []
            seen_times = set()

            for pid in p_ids:
                p_obj = photo_lookup.get(pid)
                t_str = p_obj.taken_at if p_obj else ""
                # Approximate 10-second bucket for burst suppression
                time_bucket = t_str[:18] if t_str and len(t_str) >= 18 else pid
                if time_bucket not in seen_times:
                    seen_times.add(time_bucket)
                    distinct_pids.append(pid)
                else:
                    burst_extras.append(pid)

            # Assemble group prioritizing distinct shots, padding with burst extras if needed
            selected_pids = distinct_pids[:cfg_groups.group_max]
            if len(selected_pids) < cfg_groups.group_min:
                for b_pid in burst_extras:
                    if b_pid not in selected_pids:
                        selected_pids.append(b_pid)
                    if len(selected_pids) >= cfg_groups.group_min:
                        break

            # Fallback pad from remaining candidate_ids if still below group_min
            if len(selected_pids) < cfg_groups.group_min:
                for cid in candidate_ids:
                    if cid not in selected_pids:
                        selected_pids.append(cid)
                    if len(selected_pids) >= cfg_groups.group_min:
                        break

            if len(selected_pids) >= 1:
                processed_groups.append(selected_pids)

        if not processed_groups:
            return []

        # Calculate why chips & confidence for each group
        group_results = []
        for idx, p_ids in enumerate(processed_groups, 1):
            # Compute cue frequency and mean score in this cluster
            cue_counts: Dict[str, int] = {}
            cue_scores: Dict[str, float] = {}
            for pid in p_ids:
                for cid, sc in tags_by_photo.get(pid, {}).items():
                    if sc >= 0.20:
                        cue_counts[cid] = cue_counts.get(cid, 0) + 1
                        cue_scores[cid] = cue_scores.get(cid, 0.0) + sc

            # 1. Determine primary theme label
            primary_label = None
            if pos_cues:
                for pc in pos_cues:
                    if pc in CUE_LOOKUP:
                        primary_label = CUE_LOOKUP[pc].label
                        break

            if not primary_label:
                if query and query.strip():
                    primary_label = query.strip().capitalize()
                else:
                    dominant_cue = max(cue_counts.items(), key=lambda x: x[1])[0] if cue_counts else None
                    primary_label = CUE_LOOKUP[dominant_cue].label if dominant_cue in CUE_LOOKUP else f"Album {idx}"

            # 2. Identify distinctive secondary sub-moment for this specific cluster
            candidate_secondary = []
            for cid, cnt in cue_counts.items():
                if cid in CUE_LOOKUP:
                    cue_obj = CUE_LOOKUP[cid]
                    # Exclude duplicate / identical labels
                    if cue_obj.label.lower() in primary_label.lower() or primary_label.lower() in cue_obj.label.lower():
                        continue
                    ratio = cnt / max(1, len(p_ids))
                    avg_sc = cue_scores.get(cid, 0.0) / max(1, len(p_ids))
                    if ratio >= 0.25:
                        candidate_secondary.append((cue_obj.label, ratio * avg_sc))

            candidate_secondary.sort(key=lambda x: x[1], reverse=True)
            distinct_secondary = [lbl for lbl, _ in candidate_secondary]

            # 3. Formulate natural sub-moment title without duplication
            if distinct_secondary:
                sec_name = distinct_secondary[0]
                sub_title = sec_name
                # Friendly sensory descriptors
                sec_lower = sec_name.lower()
                if "night" in sec_lower:
                    sub_title = "Night & Festive Lights"
                elif "outdoor" in sec_lower:
                    sub_title = "Outdoor Gathering"
                elif "indoor" in sec_lower:
                    sub_title = "Indoor Moments"
                elif "food" in sec_lower or "chai" in sec_lower:
                    sub_title = "Feast & Refreshments"
                elif "crowd" in sec_lower:
                    sub_title = "Crowd & Procession"
                elif "group" in sec_lower or "people" in sec_lower:
                    sub_title = "Group & Family Moments"
                elif "festival" in sec_lower or "diyas" in sec_lower or "temple" in sec_lower:
                    sub_title = "Rituals & Mandir"
                elif "daylight" in sec_lower or "sun" in sec_lower:
                    sub_title = "Daytime Celebration"

                raw_title = f"{primary_label} — {sub_title}"
            else:
                raw_title = primary_label

            # Deduplicate any repeating tokens strictly
            tokens = []
            for part in re.split(r'[·—\-]', raw_title):
                clean_p = part.strip()
                if clean_p and clean_p.lower() not in [t.lower() for t in tokens]:
                    tokens.append(clean_p)
            group_label = " — ".join(tokens) if tokens else f"Album {idx}"

            # 4. Compute unique why chips
            why_chips = []
            if primary_label:
                why_chips.append(primary_label)
            for sec in distinct_secondary[:2]:
                if sec not in why_chips:
                    why_chips.append(sec)
            why_chips = list(dict.fromkeys(why_chips))[:2]

            # Calculate confidence
            conf = compute_confidence(
                group_photo_ids=p_ids,
                positive_cues=pos_cues,
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
        for rank_idx, grp in enumerate(group_results, 1):
            cal = grp["confidence"]["calibrated"]
            band = grp["confidence"]["band"]

            if band == "highest" or rank_idx == 1:
                display_pct = min(96, max(80, int(80 + (cal - 0.35) * 30)))
            elif band == "good":
                display_pct = min(79, max(65, int(65 + (cal - 0.25) * 35)))
            elif band == "possible":
                display_pct = min(64, max(50, int(50 + (cal - 0.15) * 45)))
            else:
                display_pct = min(49, max(25, int(cal * 100)))

            if rank_idx == 1 and pos_cues and display_pct < 80:
                display_pct = 80 + min(15, len(pos_cues) * 4)

            grp["confidence"]["percentage"] = display_pct
            grp["confidence"]["percentage_label"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["display_score"] = f"Confidence Score = {display_pct}%"
            grp["confidence"]["likelihood_hint"] = "Higher score = more likely to find your image in this album"

        return group_results[:cfg_groups.groups_shown]
