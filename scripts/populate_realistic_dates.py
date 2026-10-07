"""Populate realistic, authentic timeline dates across 2025-2026 for Memory Board demo photos.

Clusters related photos by category into authentic moments:
- Oct 2026: Autumn Festivities & Events (Dussehra, performances)
- Aug 2026: Monsoon Nature & Greenery
- Jun 2026: Summer Mountain Trails & Outdoor Treks
- May 2026: Coastal Waters & Beach Getaways
- Mar 2026: Spring Street Walk & Local Dining
- Jan 2026: New Year Gathering & Night Lights
- Nov 2025: Diwali Lights & Family Celebrations
- Sep 2025: Architecture & Monument Tours
- Jul 2025: Weekend Street Food Crawl
- May 2025: Historic Forts & Heritage Sites
- Mar 2025: Colorful Spring Festivities
- Jan 2025: Winter Cozy Home & Indoor Candids
"""

import sqlite3
from datetime import datetime, timedelta
import random

conn = sqlite3.connect('data/app.db')
c = conn.cursor()

c.execute("SELECT id, path, hour_bucket FROM photos ORDER BY path ASC")
photos = c.fetchall()
print(f"Total photos to timestamp: {len(photos)}")

# Define realistic memory moments across 2025-2026
moments = [
    # 2026
    ("events", datetime(2026, 10, 5, 14, 0)),
    ("festivals", datetime(2026, 10, 2, 18, 30)),
    ("nature", datetime(2026, 8, 18, 11, 15)),
    ("outdoors", datetime(2026, 6, 22, 15, 45)),
    ("food", datetime(2026, 5, 14, 20, 10)),
    ("night", datetime(2026, 4, 10, 22, 15)),
    ("streets", datetime(2026, 3, 25, 16, 20)),
    ("people", datetime(2026, 2, 14, 13, 0)),
    # 2025
    ("monuments", datetime(2025, 12, 28, 14, 30)),
    ("festivals", datetime(2025, 11, 12, 19, 45)),
    ("home", datetime(2025, 10, 20, 12, 0)),
    ("food", datetime(2025, 9, 15, 21, 0)),
    ("outdoors", datetime(2025, 7, 8, 10, 30)),
    ("streets", datetime(2025, 5, 20, 17, 15)),
    ("monuments", datetime(2025, 3, 11, 15, 0)),
    ("extra", datetime(2025, 1, 18, 14, 0)),
]

# Group photos by category prefix
categorized = {}
for pid, ppath, hbucket in photos:
    clean_p = ppath.replace("\\", "/")
    filename = clean_p.split("/")[-1]
    cat = filename.split("_")[0] if "_" in filename else "extra"
    if cat not in categorized:
        categorized[cat] = []
    categorized[cat].append((pid, ppath, hbucket))

random.seed(42)

for cat, p_list in categorized.items():
    matching_moments = [m for m in moments if m[0] == cat]
    if not matching_moments:
        matching_moments = moments

    for idx, (pid, ppath, hbucket) in enumerate(p_list):
        base_moment = matching_moments[idx % len(matching_moments)][1]
        
        # Add realistic minute/second variations within the moment (over 1-3 days)
        day_offset = (idx // 4) % 3
        minute_offset = (idx * 7) % 60
        second_offset = (idx * 13) % 60
        
        # Match hour bucket if present
        target_hour = hbucket if hbucket is not None else base_moment.hour
        photo_dt = base_moment.replace(hour=target_hour, minute=minute_offset, second=second_offset) + timedelta(days=day_offset)
        
        date_str = photo_dt.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE photos SET taken_at = ? WHERE id = ?", (date_str, pid))

conn.commit()

# Verify timeline months
c.execute("""
    SELECT strftime('%Y-%m', taken_at) as ym, count(*) 
    FROM photos 
    GROUP BY ym 
    ORDER BY ym DESC
""")
print("\nNew Timeline Months Distribution:")
for ym, count in c.fetchall():
    print(f"  {ym}: {count} photos")

conn.close()
print("\nTimestamp update complete!")
