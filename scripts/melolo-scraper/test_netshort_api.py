#!/usr/bin/env python3
"""Quick test of Vidrama's netshort proxy endpoints."""
import requests, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Origin": "https://vidrama.asia",
    "Referer": "https://vidrama.asia/",
}

DRAMA_ID = "7021836588775127693"

tests = [
    ("Direct dramabos API", f"https://netshort.dramabos.my.id/api/home/1?lang=in"),
    ("Vidrama proxy: home", "https://vidrama.asia/api/netshort/api/home/1?lang=in"),
    ("Vidrama proxy: drama", f"https://vidrama.asia/api/netshort/api/drama/{DRAMA_ID}?lang=in"),
    ("Vidrama proxy: watch", f"https://vidrama.asia/api/netshort/api/watch/{DRAMA_ID}/1?lang=in&code=84C818C7FB184A62D5BC784A85E1401B"),
    ("Vidrama proxy: search", "https://vidrama.asia/api/netshort/api/search?lang=in&q=kabut&page=1"),
    ("Vidrama proxy: list", "https://vidrama.asia/api/netshort/api/list/1?lang=in&region=1&sort=2"),
]

for label, url in tests:
    print(f"\n=== {label} ===")
    print(f"URL: {url[:80]}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and "json" in ct:
            data = r.json()
            # Print keys and a summary
            if isinstance(data, dict):
                keys = list(data.keys())
                print(f"Keys: {keys}")
                code = data.get("code")
                if code:
                    print(f"code: {code}")
                # Drama list
                if data.get("data") and isinstance(data["data"], dict):
                    dd = data["data"]
                    if "contentInfos" in dd:
                        infos = dd["contentInfos"]
                        print(f"contentInfos count: {len(infos)}")
                        if infos:
                            first = infos[0]
                            print(f"First: {first.get('shortPlayName', 'N/A')} (ID: {first.get('shortPlayId', 'N/A')})")
                    if "dataList" in dd:
                        dl = dd["dataList"]
                        print(f"dataList count: {len(dl)}")
                # Drama detail
                if data.get("shortPlayName"):
                    print(f"Title: {data.get('shortPlayName')}")
                    print(f"Total Eps: {data.get('totalEpisode') or data.get('script')}")
                    introduce = data.get("introduce", "")
                    if introduce:
                        print(f"Description: {introduce[:100]}...")
                    labels = data.get("labelArray", [])
                    if labels:
                        genres = [l.get("labelName", "") for l in labels]
                        print(f"Genres: {genres}")
                # Watch data
                wd = data.get("data", data)
                if isinstance(wd, dict) and wd.get("videoUrl"):
                    vu = wd["videoUrl"]
                    print(f"VideoUrl: {vu[:80]}...")
                    subs = wd.get("subtitles", [])
                    if not subs and wd.get("subtitle"):
                        subs = [{"language": "id", "url": wd["subtitle"]}]
                    print(f"Subtitles: {len(subs)}")
                    for s in subs:
                        lang = s.get("language") or s.get("lang") or "?"
                        surl = s.get("url") or s.get("src") or ""
                        print(f"  - {lang}: {surl[:60]}...")
        elif r.status_code == 200:
            print(f"Content-Type: {ct}")
            print(f"Body: {r.text[:200]}")
        else:
            print(f"Body: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
