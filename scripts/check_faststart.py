"""Count episodes by URL pattern to find videos without faststart."""
import requests

API = "https://api.shortlovers.id/api"

# Get drama count
print("Fetching dramas...", flush=True)
r = requests.get(f"{API}/dramas?includeInactive=true&limit=5&page=1", timeout=60) 
data = r.json()
total_dramas = data.get("total", 0)
dramas = data.get("dramas", [])
print(f"Total dramas: {total_dramas}", flush=True)

# Sample 10 dramas across different pages
total_eps = 0
patterns = {}
sample_urls = {}

pages_to_check = [1, 3, 5, 8, 10]
all_dramas = []

for pg in pages_to_check:
    try:
        r = requests.get(f"{API}/dramas?includeInactive=true&limit=5&page={pg}", timeout=30)
        all_dramas.extend(r.json().get("dramas", []))
    except:
        pass

print(f"Sampling {len(all_dramas)} dramas from pages {pages_to_check}...\n", flush=True)

for i, drama in enumerate(all_dramas):
    try:
        er = requests.get(f"{API}/dramas/{drama['id']}/episodes", timeout=30)
        eps = er.json() if er.status_code == 200 else []
        for ep in eps:
            url = ep.get("videoUrl", "")
            total_eps += 1
            if "/episodes/" in url:
                p = "NO_FASTSTART (stream_to_r2)"
            elif "dramas/melolo/" in url:
                p = "HAS_FASTSTART (vidrama_to_r2)"
            elif "dramas/meloshort/" in url:
                p = "HAS_FASTSTART (meloshort)"
            elif "dramas/netshort/" in url:
                p = "HAS_FASTSTART (netshort)"
            elif "melolo/" in url:
                p = "MAYBE_NO (melolo/ep - parallel or 10_new)"
            else:
                p = "OTHER"
            patterns[p] = patterns.get(p, 0) + 1
            if p not in sample_urls:
                sample_urls[p] = url[:80]
        print(f"  [{i+1}] {drama.get('title','?')[:35]:35s} {len(eps):3d} eps", flush=True)
    except Exception as e:
        print(f"  [{i+1}] Error: {e}", flush=True)

print(f"\n{'='*60}")
print(f"RESULTS (sample {len(all_dramas)} of {total_dramas} dramas)")
print(f"Episodes checked: {total_eps}")
print(f"{'='*60}")
for p, c in sorted(patterns.items(), key=lambda x: -x[1]):
    pct = (c / total_eps * 100) if total_eps else 0
    print(f"  {c:4d} ({pct:5.1f}%) - {p}")
    if p in sample_urls:
        print(f"         e.g. {sample_urls[p]}")

avg = total_eps / len(all_dramas) if all_dramas else 0
print(f"\nAvg eps/drama: {avg:.1f}")
print(f"Estimated total episodes: ~{int(total_dramas * avg)}")
