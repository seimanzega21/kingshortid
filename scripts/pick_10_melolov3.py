import json
import requests
import urllib3

urllib3.disable_warnings()

with open('discovered_melolov3_new.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)

headers = {'User-Agent': 'Mozilla/5.0'}
selected_10 = []

print("Selecting 10 dramas with valid stream episodes...")

for c in candidates:
    book_id = c['book_id']
    title = c['title']
    slug = c['slug']

    try:
        url = f"https://vidrama.asia/api/melolov3/multi-video?id={book_id}&lang=id"
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        if not r.ok:
            continue
        data = r.json()
        series = data.get('series', {})
        eps = data.get('episodes', [])
        if not eps or len(eps) < 20: # Make sure it has substantial episodes
            continue

        # Check if first episode has stream_url
        if not eps[0].get('stream_url'):
            continue

        actual_title = series.get('title') or title
        total_eps = series.get('episode_count') or len(eps)

        selected_10.append({
            'id': book_id,
            'title': actual_title,
            'slug': slug,
            'totalEpisodes': total_eps,
            'status': 'pending'
        })
        print(f"[{len(selected_10)}/10] Selected: {actual_title} ({total_eps} eps) - ID: {book_id}")

        if len(selected_10) == 10:
            break
    except Exception as e:
        continue

with open('top_10_melolov3_to_scrape.json', 'w', encoding='utf-8') as f:
    json.dump(selected_10, f, indent=2, ensure_ascii=False)
