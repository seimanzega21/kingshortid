import requests, json

DRAMA_ID = "2010948201357684738" # Legenda Naga Kembali
url = f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id"

print(f"Requesting: {url}")
r = requests.get(url, timeout=20)
if r.ok:
    data = r.json()
    eps = data.get("episodes", [])
    print(f"Total episodes: {len(eps)}")
    if eps:
        # Cek keys di episode pertama
        first_ep = eps[0]
        print("\nKeys in an episode object:")
        print(first_ep.keys())
        
        # Cari apakah ada subtitle
        has_subs = False
        for ep in eps:
            if "subtitles" in ep or "subtitle" in ep:
                print(f"Found subtitle field in ep {ep.get('index')}:")
                if "subtitles" in ep: print("  subtitles:", ep["subtitles"])
                if "subtitle" in ep: print("  subtitle:", ep["subtitle"])
                has_subs = True
                break
        if not has_subs:
            print("\nNo 'subtitles' or 'subtitle' field found inside any episode object.")
            # Cek di dalam object videos
            for ep in eps[:2]:
                print(f"\nEpisode {ep.get('index')} videos details:")
                for v in ep.get("videos", []):
                    print(f"  Video keys: {v.keys()}")
                    if "subtitles" in v:
                        print(f"    Found subtitles inside video object: {v['subtitles']}")
else:
    print(f"Error: {r.status_code}")
