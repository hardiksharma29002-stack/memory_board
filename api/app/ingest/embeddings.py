"""CLIP ViT-B-32 embedding computation and management for photos and cue texts."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from ..config import EMBEDDINGS_PATH
from ..vocab import CUES

# Global cached model and cue text embeddings
_clip_model = None
_cue_text_embeddings_cache: Optional[Dict[str, np.ndarray]] = None


def get_clip_model():
    """Lazily load CLIP model."""
    global _clip_model
    if os.environ.get("MEMORY_BOARD_TEST_MODE") == "1":
        return None

    if _clip_model is not None:
        return _clip_model

    try:
        # First try sentence_transformers CLIP
        from sentence_transformers import SentenceTransformer
        _clip_model = SentenceTransformer("clip-ViT-B-32")
    except Exception:
        try:
            # Fallback to open_clip
            import open_clip
            import torch
            model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
            model.eval()
            _clip_model = {"model": model, "preprocess": preprocess, "type": "open_clip"}
        except Exception:
            _clip_model = None

    return _clip_model


def compute_image_embedding(image_path: Path) -> np.ndarray:
    """Compute 512-dim L2-normalized embedding for an image."""
    model = get_clip_model()

    if model is None:
        # Fallback dummy embedding (for test environments without CLIP)
        vec = np.random.randn(512).astype(np.float32)
        return vec / np.linalg.norm(vec)

    try:
        from sentence_transformers import SentenceTransformer
        if isinstance(model, SentenceTransformer):
            with Image.open(image_path) as img:
                emb = model.encode(img.convert("RGB"), convert_to_numpy=True)
                emb = emb.astype(np.float32)
                norm = np.linalg.norm(emb)
                return emb / (norm if norm > 0 else 1.0)
    except Exception:
        pass

    vec = np.random.randn(512).astype(np.float32)
    return vec / np.linalg.norm(vec)


def compute_text_embedding(text: str) -> np.ndarray:
    """Compute 512-dim L2-normalized CLIP embedding for a text query."""
    if not text or not text.strip():
        return np.zeros(512, dtype=np.float32)

    model = get_clip_model()
    if model is not None:
        try:
            from sentence_transformers import SentenceTransformer
            if isinstance(model, SentenceTransformer):
                emb = model.encode(text.strip(), convert_to_numpy=True).astype(np.float32)
                norm = np.linalg.norm(emb)
                return emb / (norm if norm > 0 else 1.0)
            elif isinstance(model, dict) and model.get("type") == "open_clip":
                import open_clip
                import torch
                tok = open_clip.get_tokenizer("ViT-B-32")
                tokens = tok([text.strip()])
                with torch.no_grad():
                    emb = model["model"].encode_text(tokens).cpu().numpy().astype(np.float32)[0]
                norm = np.linalg.norm(emb)
                return emb / (norm if norm > 0 else 1.0)
        except Exception:
            pass

    # Fallback deterministic pseudo-embedding based on hash
    seed = sum(ord(c) for c in text)
    rng = np.random.RandomState(seed)
    v = rng.randn(512).astype(np.float32)
    return v / np.linalg.norm(v)


def get_cue_text_embeddings() -> Dict[str, np.ndarray]:
    """Compute and cache L2-normalized embeddings for all vocabulary cue prompts."""
    global _cue_text_embeddings_cache
    if _cue_text_embeddings_cache is not None:
        return _cue_text_embeddings_cache

    model = get_clip_model()
    embeddings = {}

    if model is not None:
        try:
            from sentence_transformers import SentenceTransformer
            if isinstance(model, SentenceTransformer):
                for cue in CUES:
                    if cue.is_rule_based:
                        continue
                    emb = model.encode(cue.prompt, convert_to_numpy=True).astype(np.float32)
                    norm = np.linalg.norm(emb)
                    embeddings[cue.id] = emb / (norm if norm > 0 else 1.0)
                _cue_text_embeddings_cache = embeddings
                return embeddings
        except Exception:
            pass

    # Deterministic mock embeddings based on hash for testing / offline
    for cue in CUES:
        if cue.is_rule_based:
            continue
        seed = sum(ord(c) for c in cue.id)
        rng = np.random.RandomState(seed)
        v = rng.randn(512).astype(np.float32)
        embeddings[cue.id] = v / np.linalg.norm(v)

    _cue_text_embeddings_cache = embeddings
    return embeddings


def load_all_embeddings(path: Path = EMBEDDINGS_PATH) -> np.ndarray:
    """Load the full embedding matrix from disk."""
    if path.exists():
        return np.load(path)
    return np.empty((0, 512), dtype=np.float32)


def save_embeddings(matrix: np.ndarray, path: Path = EMBEDDINGS_PATH) -> None:
    """Save the full embedding matrix to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, matrix.astype(np.float32))
