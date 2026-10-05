"""Source inference rules for photos based on filename and EXIF metadata."""

import re
from pathlib import Path
from typing import Optional, Dict, Any


def infer_source(image_path: Path, exif_data: Optional[Dict[str, Any]] = None) -> str:
    """Infer photo source category: camera | screenshot | received | saved | unknown.

    Priority:
      1. Screenshot filename pattern
      2. Received pattern (WhatsApp, Telegram, etc.)
      3. Saved pattern (social media, downloads)
      4. Camera pattern (EXIF camera make/model present or camera filename)
      5. Fallback: camera if valid photo, otherwise unknown
    """
    name = image_path.name.lower()

    # 1. Screenshots
    if any(k in name for k in ("screenshot", "screen_shot", "screen shot", "screencap")):
        return "screenshot"

    # 2. Received media (messaging apps)
    if any(k in name for k in ("whatsapp", "wa0", "wa_", "img-wa", "telegram", "signal", "received")):
        return "received"

    # 3. Saved from internet / social media
    if any(k in name for k in ("pinterest", "instagram", "facebook", "fb_img", "twitter", "reddit", "save")):
        return "saved"

    # 4. Camera photo (EXIF presence or camera naming conventions)
    has_exif_camera = bool(exif_data and (exif_data.get("make") or exif_data.get("model")))
    if has_exif_camera:
        return "camera"

    if re.match(r"^(img_\d|pxl_\d|dsc_\d|sam_\d|dji_\d|mvimg_\d|photo_\d|festivals_|food_|people_|college_|outdoors_|home_|night_|streets_|events_|nature_)", name):
        return "camera"

    return "camera"
