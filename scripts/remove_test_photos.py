import sqlite3
import os
from pathlib import Path

conn = sqlite3.connect('data/app.db')
c = conn.cursor()

# Get all table names
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print(f"Database tables: {tables}")

# Find test photos
c.execute("SELECT id, path FROM photo WHERE instr(path, 'test_') > 0") if 'photo' in tables else c.execute("SELECT id, path FROM photos WHERE instr(path, 'test_') > 0")
test_photos = c.fetchall()
print(f"Found {len(test_photos)} test photos:")
for pid, ppath in test_photos:
    print(f"  ID: {pid}, Path: {ppath}")

photo_table = 'photo' if 'photo' in tables else 'photos'
tag_table = 'phototag' if 'phototag' in tables else 'photo_tags'
activity_table = 'photoactivity' if 'photoactivity' in tables else ('photo_activities' if 'photo_activities' in tables else None)

for pid, ppath in test_photos:
    if tag_table and tag_table in tables:
        c.execute(f"DELETE FROM {tag_table} WHERE photo_id = ?", (pid,))
    if activity_table and activity_table in tables:
        c.execute(f"DELETE FROM {activity_table} WHERE photo_id = ?", (pid,))
    c.execute(f"DELETE FROM {photo_table} WHERE id = ?", (pid,))
    
    # Remove files from disk
    clean_path = ppath.replace("\\", "/")
    for candidate in [Path(clean_path), Path("data/photos") / Path(clean_path).name]:
        if candidate.exists() and candidate.is_file():
            try:
                candidate.unlink()
                print(f"  Deleted file: {candidate}")
            except Exception as e:
                print(f"  Error deleting {candidate}: {e}")
                
    for size in (256, 1024):
        thumb_f = Path(f"data/thumbs/{pid}_{size}.webp")
        if thumb_f.exists() and thumb_f.is_file():
            try:
                thumb_f.unlink()
                print(f"  Deleted thumb: {thumb_f}")
            except Exception as e:
                print(f"  Error deleting {thumb_f}: {e}")

conn.commit()

# Verify remaining count
c.execute(f"SELECT count(*) FROM {photo_table}")
total_remaining = c.fetchone()[0]
print(f"\nCleaned successfully! Total real photos remaining in DB: {total_remaining}")
conn.close()
