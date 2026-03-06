import json
with open('scraped_data/complete_capture.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"Books: {len(d.get('books', {}))}")
print(f"Chapters: {len(d.get('chapters', {}))}")
print(f"Videos: {len(d.get('videoUrls', []))}")
print(f"API responses: {len(d.get('rawApiResponses', []))}")

# Check API responses for book data
responses = d.get('rawApiResponses', [])
print(f"\nChecking {len(responses)} API responses for book data...")

for i, r in enumerate(responses[:20]):
    body = r.get('body', '')
    if 'bookName' in body or 'coverUrl' in body or 'bookId' in body:
        print(f"\n[Response {i}] Found book data:")
        print(body[:500])
        print("---")
