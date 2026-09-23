import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
print(f"Chunks from current watch page: {len(chunks)}")

for c in set(chunks):
    chunk_url = f"https://vidrama.asia{c}"
    try:
        r = requests.get(chunk_url, headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            if 'getEpisodeUrl' in r.text:
                print(f"\nFOUND getEpisodeUrl in {c} (len={len(r.text)}):")
                # find createServerReference
                for m in re.finditer(r'createServerReference\("([a-f0-9]+)"[^)]*getEpisodeUrl', r.text):
                    print("  -> Found Action ID:", m.group(1))
                # or general occurrences
                for m in re.finditer(r'getEpisodeUrl', r.text):
                    print("  Snippet:", r.text[max(0, m.start()-60):min(len(r.text), m.end()+120)])
    except Exception as e:
        print(f"Failed {c}: {e}")
