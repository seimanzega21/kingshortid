import requests, json, re, sys
sys.stdout.reconfigure(encoding="utf-8")

url = "https://vidrama.asia/watch/99-mutiara-kasih--2804/1?provider=flareflow"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

resp = requests.get(url, headers=headers, timeout=15, verify=False)
if not resp.ok:
    print(f"Failed to fetch {url}, status: {resp.status_code}")
    sys.exit(1)

html = resp.text
# Look for next-action in chunks. Usually it looks like: action: "xxxx"
# Or in <form action="javascript:throw new Error('A React form was unexpectedly submitted...')">
# Let's search for any 40-character hex string which is typical for next-action
action_id = None
matches = re.findall(r'([a-f0-9]{40})', html)
if matches:
    # Most frequent 40-char hex is usually the next-action
    from collections import Counter
    c = Counter(matches)
    action_id = c.most_common(1)[0][0]
    print(f"Found possible next-action: {action_id}")
else:
    print("Could not find next-action ID")
    sys.exit(1)

# Now send POST request
headers.update({
    "next-action": action_id,
    "accept": "text/x-component",
    "content-type": "text/plain;charset=UTF-8",
    "origin": "https://vidrama.asia",
    "referer": url,
})
resp2 = requests.post(url, headers=headers, data=json.dumps(["2804"]).encode("utf-8"), timeout=15, verify=False)

if resp2.ok:
    print("POST successful!")
    # Parse the RSC format
    for line in resp2.text.split('\n'):
        if 'episodes' in line or 'videos' in line:
            print(line[:1000])
else:
    print(f"POST failed with {resp2.status_code}")
    print(resp2.text[:500])
