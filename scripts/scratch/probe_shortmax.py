import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

# 1. First probe potential endpoints
endpoints = [
    'https://vidrama.asia/api/shortmax/detail?id=864494',
    'https://vidrama.asia/api/shortmax/detail/864494',
    'https://vidrama.asia/api/shortmax/drama/864494',
    'https://vidrama.asia/api/shortmax?action=detail&id=864494',
    'https://vidrama.asia/api/shortmax/episodes/864494',
    'https://vidrama.asia/api/shortmax/video?bookId=864494&episode=1',
    'https://vidrama.asia/api/shortmax/episode?id=864494&ep=1',
    'https://vidrama.asia/api/shortmax/watch?bookId=864494&episode=1',
    'https://vidrama.asia/api/proxy-shortmax/detail/864494',
    'https://vidrama.asia/api/proxy-shortmax/episodes/864494',
    'https://vidrama.asia/api/proxy-shortmax/watch?bookId=864494&episode=1',
    'https://vidrama.asia/api/shortmax/play?id=864494&episode=1',
    'https://vidrama.asia/api/shortmax/multi-video?id=864494&lang=id',
    'https://vidrama.asia/api/shortmax?action=stream&id=864494&episode=1',
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=headers, timeout=5, verify=False)
        print(f"[{r.status_code}] {ep}")
        if r.status_code == 200:
            print("  Response:", r.text[:200])
    except Exception as e:
        print(f"[ERR] {ep}: {e}")

# 2. Extract and inspect JS chunks from watch page
print("\n--- Inspecting JS chunks from watch page ---")
with open('watch_shortmax.html', 'r', encoding='utf-8') as f:
    watch_html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', watch_html)
print(f"Found {len(chunks)} chunks.")

for chunk in set(chunks):
    chunk_url = f"https://vidrama.asia{chunk}"
    try:
        cr = requests.get(chunk_url, headers=headers, timeout=10, verify=False)
        text = cr.text
        if 'shortmax' in text.lower():
            print(f"Found 'shortmax' in {chunk}:")
            matches = re.findall(r'["\'](/api/[^"\']+)["\']', text)
            for m in matches:
                print(f"  API in chunk: {m}")
            # Also look for keywords around shortmax
            for m in re.finditer(r'shortmax', text, re.IGNORECASE):
                snippet = text[max(0, m.start()-50):min(len(text), m.end()+100)]
                print(f"  Context: {snippet}")
    except Exception as e:
        pass
