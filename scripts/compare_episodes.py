import requests, json

# Get Vidrama episode details
r = requests.get("https://vidrama.asia/api/melolo?action=detail&id=7588815593659173941", timeout=15)
d = r.json()["data"]
vidrama_eps = d.get("episodes", [])

# Get our DB episodes
r2 = requests.get("https://api.shortlovers.id/api/dramas/cmleexll8004hhx5e4qx99qtv/episodes", timeout=15)
our_eps = r2.json()
our_eps.sort(key=lambda x: x.get("episodeNumber", 0))

out = []
out.append(f"Vidrama: {len(vidrama_eps)} episodes")
out.append(f"Our DB: {len(our_eps)} episodes")
out.append("")
out.append("VIDRAMA (first 5):")
for i, e in enumerate(vidrama_eps[:5]):
    out.append(f"  EP{i+1}: duration={e.get('duration','?')}s")

out.append("")
out.append("OUR DB (first 5):")
for e in our_eps[:5]:
    num = e.get("episodeNumber", "?")
    dur = e.get("duration", "?")
    url = e.get("videoUrl", "")
    ep_folder = url.split("/")[-2] if "/" in url else "?"
    out.append(f"  EP{num}: duration={dur}s, folder={ep_folder}")
    out.append(f"    url={url}")

out.append("")
out.append("VIDEO ACCESSIBILITY:")
for e in our_eps[:3]:
    num = e.get("episodeNumber")
    url = e.get("videoUrl", "")
    try:
        r = requests.head(url, timeout=10)
        size = int(r.headers.get("content-length", 0))
        out.append(f"  EP{num}: HTTP {r.status_code} ({size} bytes)")
    except Exception as ex:
        out.append(f"  EP{num}: ERROR - {ex}")

with open("episode_comparison.txt", "w") as f:
    f.write("\n".join(out))
print("Written to episode_comparison.txt")
