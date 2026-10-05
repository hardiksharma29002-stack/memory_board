"""Face detection module (stores count only, strictly no biometric data or crops)."""

from pathlib import Path
from PIL import Image
import numpy as np

# Lazy global detector instance
_detector = None
_init_attempted = False


def _get_mediapipe_detector():
    """Lazily initialize MediaPipe face detector."""
    global _detector, _init_attempted
    if _init_attempted:
        return _detector

    _init_attempted = True
    try:
        import mediapipe as mp
        mp_face_detection = mp.solutions.face_detection
        _detector = mp_face_detection.FaceDetection(
            model_selection=1,  # 0 for short range (<2m), 1 for full range (<5m)
            min_detection_confidence=0.5,
        )
    except Exception:
        _detector = None
    return _detector


def count_faces(image_path: Path) -> int:
    """Detect faces and return count. Strictly returns integer count only."""
    detector = _get_mediapipe_detector()
    if detector is None:
        return 0

    try:
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB")
            # Downsample if image is huge for speed
            if max(rgb_img.size) > 1280:
                rgb_img.thumbnail((1280, 1280), Image.Resampling.BILINEAR)
            img_arr = np.array(rgb_img)

        results = detector.process(img_arr)
        if results and results.detections:
            return len(results.detections)
        return 0
    except Exception:
        return 0
