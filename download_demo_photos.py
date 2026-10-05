"""Download authentic Indian daily-life photos from Wikimedia Commons.

NO API KEY NEEDED. 100% free, public domain & Creative Commons licensed.

Usage:
    python download_demo_photos.py [count]
    (defaults to 150 photos, or pass 500 for full dataset)

Photos are automatically saved and organized into: data/photos/
"""

import os
import sys
import time
import json
import re
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = Path(__file__).parent / "data" / "photos"
USER_AGENT = "MemoryBoardPhotoDataset/1.0 (https://github.com; memoryboard@example.com)"

# Search queries mapped to cognitive cue groups and Indian daily moments
CATEGORIES = [
    # 🪔 Festivals & celebrations
    ("festivals", [
        "Diwali festival celebration",
        "Holi festival colors India",
        "Indian wedding ceremony rituals",
        "Rangoli decoration festival",
        "Puja festival India traditional",
        "Durga puja celebration",
        "Ganesh Chaturthi festival India",
        "Navratri garba dance celebration",
        "Onam boat race festival Kerala",
    ]),

    # 🍛 Food & chai
    ("food", [
        "Indian street food stall vendor",
        "Chai tea stall India",
        "Indian thali traditional meal",
        "Samosa snack India",
        "Dosa South Indian food",
        "Biryani Indian cuisine",
        "Pani puri street food India",
        "Jalebi sweets India vendor",
        "Indian sweets mithai shop",
    ]),

    # 👨‍👩‍👧‍👦 People & gatherings
    ("people", [
        "Indian family gathering celebration",
        "Indian friends group outdoors",
        "Indian students college campus",
        "People of India portrait street",
        "Indian children playing",
        "Indian wedding guests dancing",
        "Laughing people India candid",
    ]),

    # 🌅 Outdoors & travel
    ("outdoors", [
        "Varanasi ghats river Ganga",
        "Indian temple architecture historical",
        "Indian railway train travel",
        "Goa beach sunset India",
        "Himalayas landscape Himachal Ladakh",
        "Rooftop view city India",
        "Hampi ruins Karnataka landscape",
        "Udaipur lake palace sunset",
        "Kashmir Dal lake shikara boat",
    ]),

    # 🏠 Home & daily moments
    ("home", [
        "Indian home living room interior",
        "Balcony view Indian city morning",
        "Rural village house India daily life",
        "Indian kitchen cooking",
        "Courtyard traditional Indian home",
    ]),

    # 🌃 Night & city lights
    ("night", [
        "Indian city night street lights",
        "Diwali night diyas oil lamps",
        "Indian night market bazaar illuminated",
        "Marine Drive Mumbai night",
        "Golden Temple Amritsar night lighting",
        "Mysore Palace illumination night",
    ]),

    # 🛺 Markets & streets
    ("streets", [
        "Auto rickshaw street traffic India",
        "Indian bazaar vegetable market colorful",
        "Old Delhi crowded street market",
        "Street vendor cart India",
        "Flower market marigold garlands India",
        "Kolkata yellow taxi Howrah",
        "Mumbai local train commuters",
    ]),

    # 🏏 Events & culture
    ("events", [
        "Indian classical dance performance stage",
        "Cricket match playing India ground",
        "Mehendi ceremony hands wedding",
        "College festival stage event India",
        "Music concert stage India festival",
        "Dussehra festival India effigy",
        "Eid celebration India Jama Masjid",
    ]),

    # 🌿 Nature & greenery
    ("nature", [
        "Monsoon rain landscape India",
        "Indian village agricultural field green",
        "Kerala backwaters palm trees",
        "Public garden park India flowers",
        "Tea gardens Munnar hills green",
        "Peacock national bird India",
        "Bangalore Cubbon Park trees",
        "Darjeeling tea plantation hills",
    ]),

    # 🏛️ Architecture & Heritage
    ("monuments", [
        "Taj Mahal Agra India morning",
        "Qutub Minar Delhi monument",
        "Red Fort Delhi architecture",
        "Hawa Mahal Jaipur pink city",
        "Gateway of India Mumbai harbor",
        "Meenakshi Amman temple Madurai",
        "Jodhpur blue city Rajasthan",
        "Rishikesh Ganga river bridge",
        "Goa church Portuguese architecture",
        "Ladakh Pangong lake mountains",
        "Shimla Himachal snow landscape",
        "Chennai Marina beach evening",
    ]),
]

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"


def search_wikimedia_images(query: str, limit: int = 15) -> list[dict]:
    """Search Wikimedia Commons for high-quality photos matching query."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{query}",
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": min(limit * 2, 40),
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": 1024,  # Get ~1024px scaled Web-ready image
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(WIKIMEDIA_API, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})

        results = []
        for page_id, page_data in pages.items():
            imageinfo = page_data.get("imageinfo", [])
            if not imageinfo:
                continue

            info = imageinfo[0]
            mime = info.get("mime", "").lower()
            if mime not in ("image/jpeg", "image/jpg", "image/png", "image/webp"):
                continue

            # Prefer thumburl (1024px width) over massive original files
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue

            title = page_data.get("title", f"file_{page_id}")
            results.append({
                "url": url,
                "title": title,
                "page_id": page_id,
            })
            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f"  ⚠ Query '{query}' failed: {e}")
        return []


def download_single_photo(url: str, filepath: Path) -> bool:
    """Download photo from URL and write to disk."""
    if filepath.exists() and filepath.stat().st_size > 5000:
        return True  # Already downloaded

    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=25)
        resp.raise_for_status()
        if len(resp.content) < 5000:  # Skip corrupt/tiny files
            return False

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(resp.content)
        return True
    except Exception:
        return False


def main():
    target_count = 150
    if len(sys.argv) > 1:
        try:
            target_count = int(sys.argv[1])
        except ValueError:
            pass

    print("=" * 65)
    print("  📷 Memory Board — Demo Photo Downloader (Wikimedia Commons)")
    print("  ✨ Free, open license, NO API KEY REQUIRED!")
    print(f"  Target: ~{target_count} authentic Indian daily-life photos")
    print(f"  Destination: {OUTPUT_DIR.resolve()}")
    print("=" * 65 + "\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine per-query quota
    total_queries = sum(len(queries) for _, queries in CATEGORIES)
    per_query_target = max(3, target_count // total_queries + 1)

    all_tasks = []
    seen_urls = set()

    print("🔍 Discovering photos across categories...")
    for category_name, queries in CATEGORIES:
        print(f"\n📁 [{category_name.upper()}]")
        for q in queries:
            if len(all_tasks) >= target_count:
                break
            print(f"  • Searching: '{q}'...", end=" ", flush=True)
            results = search_wikimedia_images(q, limit=per_query_target)
            added = 0
            for item in results:
                url = item["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Clean filename
                clean_title = re.sub(r"[^\w\-_.]", "_", item["title"])[:50]
                if not clean_title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    clean_title += ".jpg"
                filename = f"{category_name}_{item['page_id']}_{clean_title}"
                filepath = OUTPUT_DIR / filename

                all_tasks.append((url, filepath, category_name))
                added += 1
                if len(all_tasks) >= target_count:
                    break

            print(f"found {added} photos")
            time.sleep(0.3)  # Respectful rate limit

        if len(all_tasks) >= target_count:
            break

    print(f"\n📥 Starting parallel download of {len(all_tasks)} photos...\n")

    downloaded = 0
    skipped = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(download_single_photo, url, fp): (url, fp, cat)
            for url, fp, cat in all_tasks
        }

        total_jobs = len(futures)
        for i, future in enumerate(as_completed(futures), 1):
            url, fp, cat = futures[future]
            try:
                success = future.result()
                if success:
                    downloaded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            pct = int((i / total_jobs) * 100)
            bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
            print(f"\r  [{bar}] {pct}% ({i}/{total_jobs})", end="", flush=True)

    print("\n\n" + "=" * 65)
    print("  ✅ Download Complete!")
    print(f"  📷 Downloaded: {downloaded}")
    print(f"  ❌ Failed:     {failed}")
    print(f"  📂 Saved in:   {OUTPUT_DIR.resolve()}")
    print("=" * 65 + "\n")

    # Save dataset info
    info = {
        "source": "Wikimedia Commons (Creative Commons / Public Domain)",
        "downloaded_count": downloaded,
        "categories": [c for c, _ in CATEGORIES],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (OUTPUT_DIR / "_dataset_info.json").write_text(json.dumps(info, indent=2))

    # Breakdown by category
    print("  Category Breakdown:")
    breakdown = {}
    for f in OUTPUT_DIR.glob("*.jpg"):
        cat = f.name.split("_")[0]
        breakdown[cat] = breakdown.get(cat, 0) + 1
    for cat, cnt in sorted(breakdown.items()):
        print(f"    {cat:15s}: {cnt} photos")

    print("\n  👉 Next step: Run 'make ingest' to index these photos into Memory Board!")


if __name__ == "__main__":
    main()
