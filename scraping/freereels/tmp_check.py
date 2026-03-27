import json

d = json.load(open('d:/kingshortid/scraping/freereels/pipeline_v2_status.json', 'r', encoding='utf-8'))

print("=== INCOMPLETE DRAMAS ===")
for k, v in d.items():
    if not v.get('complete'):
        print(f"  {v['title']}: {v['uploaded']}/{v['total']} eps")

print("\n=== COMPLETE DRAMAS ===")
for k, v in d.items():
    if v.get('complete'):
        print(f"  {v['title']}: {v['uploaded']}/{v['total']} eps")
