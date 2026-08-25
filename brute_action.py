import re, requests, json

url_page = 'https://vidrama.asia/movie/dijulukisang-pembangkit-negara--843859?provider=shortmax&lang=id'
html = requests.get(url_page, headers={'User-Agent':'Mozilla/5.0'}).text
chunks = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', html)
print(f"Found {len(chunks)} chunks.")

action_ids = set()
for c in chunks:
    try:
        js = requests.get('https://vidrama.asia' + c).text
        actions = re.findall(r'([a-f0-9]{40})', js)
        action_ids.update(actions)
    except: pass

print(f"Found {len(action_ids)} possible Action IDs.")

url_post = 'https://vidrama.asia/en/watch/slug--843859/1?provider=shortmax'
for aid in action_ids:
    hdrs = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/x-component',
        'next-action': aid
    }
    try:
        r = requests.post(url_post, headers=hdrs, data=json.dumps(["843859", "id"]), timeout=5)
        if r.status_code == 200:
            print(f"SUCCESS! Action ID is: {aid}")
            print(r.text[:200])
            break
        elif r.status_code != 404 and r.status_code != 500:
            print(f"Interesting status {r.status_code} for {aid}")
    except Exception as e:
        pass
