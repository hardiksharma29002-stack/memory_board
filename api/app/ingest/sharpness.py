"""Sharpness and brightness computation."""

from pathlib import Path
from typing import Tuple
import numpy as np
from PIL import Image


def compute_sharpness_and_brightness(image_path: Path) -> Tuple[float, float]:
    """Compute Laplacian variance (sharpness) and mean brightness (0.0 - 1.0)."""
    try:
        with Image.open(image_path) as img:
            # Grayscale conversion
            gray = img.convert("L")
            # Downsample slightly to max 512 for fast processing
            if max(gray.size) > 512:
                gray.thumbnail((512, 512), Image.Resampling.BILINEAR)

            arr = np.array(gray, dtype=np.float32)

            # Mean brightness scaled to [0.0, 1.0]
            brightness = float(np.mean(arr) / 255.0)

            # Laplacian kernel convolution for sharpness
            # [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
            if arr.shape[0] >= 3 and arr.shape[1] >= 3:
                laplacian = (
                    arr[:-2, 1:-1]
                    + arr[2:, 1:-1]
                    + arr[1:-1, :-2]
                    + arr[1:-1, 2:]
                    - 4 * arr[1:-1, 1:-1]
                )
                sharpness = float(np.var(laplacian))
            else:
                sharpness = 0.0

            return round(sharpness, 2), round(brightness, 4)

    except Exception:
        return 0.0, 0.5
