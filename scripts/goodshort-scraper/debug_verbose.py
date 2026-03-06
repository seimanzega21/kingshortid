"""Ultra verbose import for debugging"""
import psycopg2
import json
from pathlib import Path

DATABASE_URL = "postgresql://postgres:seiman21@localhost:5432/kingshort"
R2_PUBLIC_URL = "https://stream.shortlovers.id"
SOURCE_DIR = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

print("=== STARTING IMPORT ===\n")
print(f"Source directory: {SOURCE_DIR}")
print(f"Directory exists: {SOURCE_DIR.exists()}\n")

# List folders
folders = [f for f in SOURCE_DIR.iterdir() if f.is_dir()]
print(f"Found {len(folders)} drama folders:")
for f in folders:
    print(f"  - {f.name}")
print()

# Process first folder only for testing
test_folder = folders[0]
print(f"=== PROCESSING TEST: {test_folder.name} ===\n")

metadata_file = test_folder / "metadata.json"
print(f"Metadata file: {metadata_file}")
print(f"Exists: {metadata_file.exists()}\n")

with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

book_id = metadata['bookId']
title = metadata['title']

print(f"Title: {title}")
print(f"BookID: {book_id}\n")

# Connect and check if exists
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Testing drama_exists query...")
query = 'SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1'
param = (f'%{book_id}%',)
print(f"Query: {query}")  
print(f"Param: {param}\n")

cur.execute(query, param)
result = cur.fetchone()

print(f"Query result: {result}")

if result:
    print(f"\n❌ DRAMA EXISTS - Will be skipped!")
    print(f"   Drama ID: {result[0]}\n")
    
    # Get details
    cur.execute(f'SELECT title, description FROM "Drama" WHERE id = \'{result[0]}\'')
    details = cur.fetchone()
    print(f"   Existing title: {details[0]}")
    print(f"   Description: {details[1][:200]}...")
else:
    print(f"\n✅ DRAMA DOES NOT EXIST - Will be imported!")

conn.close()
