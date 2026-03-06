import requests, json

BACKEND = "https://api.shortlovers.id/api"
VIDRAMA = "https://vidrama.asia/api/melolo"

titles = [
    "Sistem Harta Tersembunyi",
    "Aku Kaya Dari Giok",
    "Pulang Kampung Bawa CEO",
    "Bersinar Setelah Cerai",
    "Ahli Pengobatan Sakti",
]

# Get all dramas from backend
r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=15)
all_dramas = r.json().get("dramas", r.json() if isinstance(r.json(), list) else [])

out = []
for t in titles:
    match = next((d for d in all_dramas if d.get("title","").lower() == t.lower()), None)
    if match:
        out.append(f"{t}")
        out.append(f"  id: {match['id']}")
        out.append(f"  slug: {match.get('slug','?')}")
        out.append(f"  cover: {match.get('cover','?')}")
        # Check cover accessibility
        cover = match.get("cover", "")
        if cover:
            try:
                cr = requests.head(cover, timeout=10)
                out.append(f"  cover status: HTTP {cr.status_code}")
            except:
                out.append(f"  cover status: ERROR")
    else:
        out.append(f"{t} -> NOT FOUND IN DB")
    out.append("")

with open("cover_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Written to cover_check.txt")
