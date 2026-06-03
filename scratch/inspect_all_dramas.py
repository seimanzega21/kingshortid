import json

with open('all_dramas.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print("Type of all_dramas.json content:", type(d))
if isinstance(d, dict):
    print("Keys:", list(d.keys()))
    for k, v in d.items():
        print(f"Key '{k}' type: {type(v)}")
        if isinstance(v, list):
            print(f"  Length: {len(v)}")
            if v:
                print(f"  Sample: {v[0]}")
elif isinstance(d, list):
    print("Length:", len(d))
    if d:
        print("Sample 0:", d[0])
