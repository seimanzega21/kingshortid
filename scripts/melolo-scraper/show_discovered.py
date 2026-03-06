import json, sys
sys.stdout.reconfigure(encoding="utf-8")
with open("microdrama_id_dramas.json", "r", encoding="utf-8") as f:
    dramas = json.load(f)
print(f"Total Indonesian dramas found: {len(dramas)}")
print()
for i, d in enumerate(dramas[:30], 1):
    print(f"{i:3}. {d['title']} ({d.get('episodes', '?')} eps)")
