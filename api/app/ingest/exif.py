"""EXIF metadata extraction and hour bucket computation."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ExifTags


EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}


def extract_exif(image_path: Path, brightness: Optional[float] = None) -> Dict[str, Any]:
    """Extract EXIF metadata: taken_at, make, model, width, height, and hour_bucket."""
    result: Dict[str, Any] = {
        "taken_at": None,
        "hour_bucket": None,
        "make": None,
        "model": None,
        "width": 0,
        "height": 0,
    }

    try:
        with Image.open(image_path) as img:
            result["width"], result["height"] = img.size
            exif_data = img.getexif()

            if exif_data:
                # Check for DateTimeOriginal in standard EXIF or IFD
                date_str = None
                # Tag 36867 = DateTimeOriginal, Tag 306 = DateTime
                if 36867 in exif_data:
                    date_str = str(exif_data[36867])
                elif 306 in exif_data:
                    date_str = str(exif_data[306])
                else:
                    # Check in Exif IFD
                    try:
                        exif_ifd = exif_data.get_ifd(0x8769)
                        if exif_ifd:
                            if 36867 in exif_ifd:
                                date_str = str(exif_ifd[36867])
                            elif 36868 in exif_ifd:
                                date_str = str(exif_ifd[36868])
                    except Exception:
                        pass

                if date_str:
                    try:
                        dt = datetime.strptime(date_str.strip(), "%Y:%m:%d %H:%M:%S")
                        result["taken_at"] = dt.isoformat()
                        result["hour_bucket"] = dt.hour
                    except ValueError:
                        pass

                # Make & Model
                if 271 in exif_data:
                    result["make"] = str(exif_data[271]).strip()
                if 272 in exif_data:
                    result["model"] = str(exif_data[272]).strip()

    except Exception:
        pass

    # Fallback for hour_bucket if not found in EXIF
    if result["hour_bucket"] is None and brightness is not None:
        # If very dark (< 0.25), infer night (22:00)
        # If dark (0.25 - 0.40), infer evening/dawn (18:00)
        # If bright (> 0.40), infer daytime afternoon (14:00)
        if brightness < 0.25:
            result["hour_bucket"] = 22
        elif brightness < 0.40:
            result["hour_bucket"] = 18
        else:
            result["hour_bucket"] = 14

    return result
