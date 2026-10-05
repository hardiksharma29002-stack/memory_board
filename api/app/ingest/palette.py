"""Color palette extraction using k-means clustering."""

import json
from pathlib import Path
from typing import List
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Format RGB integers to a hex color string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def extract_palette(image_path: Path, k: int = 3) -> List[str]:
    """Downsample image to 64x64 and extract k dominant colors as hex strings."""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            # Downsample to 64x64 for speed
            small = img.resize((64, 64), Image.Resampling.BILINEAR)
            pixels = np.array(small).reshape(-1, 3)

        # Run k-means
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=3)
        kmeans.fit(pixels)

        # Order clusters by frequency (largest cluster first)
        counts = np.bincount(kmeans.labels_, minlength=k)
        sorted_indices = np.argsort(counts)[::-1]

        palette = [
            rgb_to_hex(*kmeans.cluster_centers_[i])
            for i in sorted_indices[:k]
        ]

        # Ensure exactly k colors
        while len(palette) < k:
            palette.append("#808080")

        return palette

    except Exception:
        # Fallback neutral palette if extraction fails
        return ["#808080", "#a0a0a0", "#c0c0c0"][:k]


def palette_to_json(palette: List[str]) -> str:
    """Serialize palette list to JSON string."""
    return json.dumps(palette)
