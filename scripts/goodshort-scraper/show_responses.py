import json

with open('scraped_data/complete_capture.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

responses = d.get('rawApiResponses', [])
print(f"Total API responses: {len(responses)}\n")

for i, r in enumerate(responses):
    body = r.get('body', '')
    url = r.get('url', 'unknown')
    
    print(f"\n=== Response {i} ===")
    print(f"URL: {url[:60] if url else 'N/A'}")
    print(f"Body preview:\n{body[:800]}")
    print("-" * 60)
