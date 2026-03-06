import json

har = json.load(open('HTTPToolkit_2026-02-02_23-24.har', encoding='utf-8'))
entries = har['log']['entries']

# Find chapter/list calls
chapter_calls = [e for e in entries if '/chapter/list' in e['request']['url']]

print(f"Found {len(chapter_calls)} chapter/list calls\n")

if chapter_calls:
    sample = chapter_calls[0]
    resp_text = sample['response']['content'].get('text', '')
    if resp_text:
        data = json.loads(resp_text)
        print("Response structure:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
