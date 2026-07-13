import requests, re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

url = "https://vidrama.asia/provider/flareflow"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, verify=False, timeout=15)
if resp.ok:
    html = resp.text
    print(f"Fetched {url} - {len(html)} bytes")
    
    # Try to find API routes or fetch URLs
    print("\nURLs found in HTML:")
    api_urls = re.findall(r'https://[^"\']*?api[^"\']*', html)
    for u in set(api_urls):
        print("API:", u)
        
    other_urls = re.findall(r'https://[^"\']*?flareflow[^"\']*', html)
    for u in set(other_urls):
        print("Flareflow URL:", u)
        
    # Check for next-action or anything that looks like an API call
    actions = re.findall(r'action(?:s)?[\s:]+["\']([a-f0-9]{40})["\']', html)
    if actions:
        print("\nPossible next-actions:")
        for a in set(actions):
            print(a)
            
    # Try to extract RSC
    print("\nRSC Data chunks:")
    matches = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
    for i, m in enumerate(matches):
        try:
            s = m.encode('utf-8').decode('unicode_escape')
            if 'flareflow' in s.lower() or 'api' in s.lower():
                print(f"Chunk {i}: {s[:300]}...")
        except:
            pass

else:
    print(f"Error fetching {url}: {resp.status_code}")
