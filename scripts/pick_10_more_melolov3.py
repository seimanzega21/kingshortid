import json
import requests
import urllib3

urllib3.disable_warnings()

# Read already selected 10
with open('top_10_melolov3_to_scrape.json', 'r', encoding='utf-8') as f:
    first_10 = json.load(f)
selected_ids = {x['id'] for x in first_10}

# Read candidate pool
with open('discovered_melolov3_new.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)

headers = {'User-Agent': 'Mozilla/5.0'}
additional_10 = []

print("Selecting 10 more fresh dramas with valid stream episodes...")

for c in candidates:
    book_id = c['book_id']
    title = c['title']
    slug = c['slug']

    if book_id in selected_ids:
        continue

    try:
        url = f"https://vidrama.asia/api/melolov3/multi-video?id={book_id}&lang=id"
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        if not r.ok:
            continue
        data = r.json()
        series = data.get('series', {})
        eps = data.get('episodes', [])
        if not eps or len(eps) < 20:
            continue

        # Check if first episode has stream_url
        if not eps[0].get('stream_url'):
            continue

        actual_title = series.get('title') or title
        total_eps = series.get('episode_count') or len(eps)

        additional_10.append({
            'id': book_id,
            'title': actual_title,
            'slug': slug,
            'totalEpisodes': total_eps,
            'status': 'pending'
        })
        print(f"[{len(additional_10)}/10] Selected: {actual_title} ({total_eps} eps) - ID: {book_id}")

        if len(additional_10) == 10:
            break
    except Exception as e:
        continue

with open('top_10_additional_melolov3.json', 'w', encoding='utf-8') as f:
    json.dump(additional_10, f, indent=2, ensure_ascii=False)
