import requests
import re

url = "https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax"
r = requests.get(url)

# The episodes are usually rendered as links: /watch/dubbingsopir-taksi-mantan-dewa-balap--846959/2?provider=shortmax
matches = re.findall(r'/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/(\d+)\?provider=shortmax', r.text)
if matches:
    eps = [int(m) for m in matches]
    print(f"Total episodes found: {max(eps)}")
else:
    print("No episode links found.")

# Let's also check if there is episodeCount or total_episodes
eps_match = re.search(r'episodeCount["\']?\s*:\s*(\d+)', r.text)
if eps_match:
    print(f"episodeCount: {eps_match.group(1)}")
