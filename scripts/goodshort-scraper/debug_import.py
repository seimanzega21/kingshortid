import psycopg2
import json
from pathlib import Path

# Connect to database
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check for existing dramas with exact titles
titles_to_check = [
    "Cinta di Waktu yang Tepat",
    "Hidup Kedua, Cinta Sejati Menanti"
]

print("=== Checking for existing dramas ===\n")
for title in titles_to_check:
    cur.execute('SELECT id, title FROM "Drama" WHERE title = %s', (title,))
    result = cur.fetchone()
    if result:
        print(f"✓ FOUND: {result[1]} (id: {result[0]})")
    else:
        print(f"✗ NOT FOUND: {title}")

# Check metadata files
print("\n=== Checking metadata files ===\n")
r2_ready = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

for folder in r2_ready.iterdir():
    if not folder.is_dir():
        continue
    
    metadata_file = folder / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        book_id = metadata.get('bookId', '')
        title = metadata.get('title', '')
        total_eps = metadata.get('total_episodes', 0)
        episodes = metadata.get('episodes', [])
        
        print(f"Folder: {folder.name}")
        print(f"  Title: {title}")
        print(f"  BookID: {book_id}")
        print(f"  Total Episodes (metadata): {total_eps}")
        print(f"  Episodes array length: {len(episodes)}")
        
        # Count episodes with video_url
        valid_eps = sum(1 for ep in episodes if ep.get('video_url'))
        print(f"  Episodes with video_url: {valid_eps}")
        print()

conn.close()
