import requests

BACKEND = "https://api.shortlovers.id/api"

# Titles we fixed covers for - search for duplicates
search_terms = [
    "sistem harta",
    "aku kaya",
    "pulang kampung",
    "bersinar setelah",
    "ahli pengobatan",
]

r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=15)
all_dramas = r.json().get("dramas", [])
if not all_dramas and isinstance(r.json(), list):
    all_dramas = r.json()

out = []
duplicates = []

for term in search_terms:
    matches = [d for d in all_dramas if term.lower() in d.get("title","").lower()]
    if len(matches) > 1:
        out.append(f"⚠️ DUPLICATE: '{term}' -> {len(matches)} entries:")
        for m in matches:
            eps = m.get("totalEpisodes", 0)
            out.append(f"  - id={m['id']}, title='{m['title']}', eps={eps}, cover={m.get('cover','')[-40:]}")
            if eps == 0:
                duplicates.append(m)
    elif len(matches) == 1:
        out.append(f"✅ OK: '{matches[0]['title']}' (1 entry, eps={matches[0].get('totalEpisodes',0)})")
    else:
        out.append(f"❌ NOT FOUND: '{term}'")
    out.append("")

out.append(f"\nDuplicates to delete: {len(duplicates)}")
for d in duplicates:
    out.append(f"  DELETE: id={d['id']}, title='{d['title']}', eps={d.get('totalEpisodes',0)}")

with open("duplicate_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Written to duplicate_check.txt")
