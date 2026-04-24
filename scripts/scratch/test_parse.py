import requests
import re
import json

r = requests.get('https://vidrama.asia/provider/idrama')
matches = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', r.text)

print(f"Found {len(matches)} chunks")
for idx, m in enumerate(matches):
    try:
        data = json.loads(m)
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], str):
            text = data[1]
            if "tiga-tahun-diam" in text:
                print(f"Found drama slug in chunk {idx}")
                # We can see the shape of the json payload
                # Usually it's in a format like [{"title":"...","slug":"..."}, ...] embedded inside the string
                # We can just regex out the dicts directly since they use Next.js RSC wire format
                break
    except Exception as e:
        print(f"Error parsing chunk {idx}: {e}")

# Since RSC parsing is extremely difficult (it has backreferences like "$1", "$2"),
# a simpler way is to extract strings that look like slugs from the page!
# Any string that matches [a-z0-9-]+ and appears in href="/provider/idrama/slug" or href="/[slug]"
slugs = re.findall(r'href="/([^/"]+)"', r.text)
# the actual URL format on vidrama is href="/tiga-tahun-diam-hari-ini-aku-bangkit"
print("Slugs found:", list(set(slugs)))
