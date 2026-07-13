import requests, json, re, sys
sys.stdout.reconfigure(encoding="utf-8")

url = "https://vidrama.asia/watch/99-mutiara-kasih--2804/1?provider=flareflow"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

resp = requests.get(url, headers=headers, timeout=15, verify=False)
if resp.ok:
    html = resp.text
    matches = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
    found = False
    for m in matches:
        try:
            if "videos" in m or "quality" in m or "subtitles" in m:
                # Unescape string
                s = m.encode('utf-8').decode('unicode_escape')
                if "videos" in s:
                    print("Found videos payload!")
                    print(s[:500])
                    found = True
        except:
            pass
    if not found:
        print("No videos found in watch page.")
else:
    print(resp.status_code)
