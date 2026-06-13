import json

with open("scratch/serigala_search_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

dramas = data.get('results', [])
if dramas:
    # Let's inspect the keys of the first drama matching "Aku Lahirkan Anak Serigala Presiden"
    target = next((d for d in dramas if "Serigala" in d.get('short_play_name', '')), dramas[0])
    print("Drama Title:", target.get('short_play_name'))
    print("Keys of drama object:")
    for k in sorted(list(target.keys())):
        val = target[k]
        val_type = type(val).__name__
        if isinstance(val, (dict, list)):
            val_desc = f"length {len(val)}"
        else:
            val_desc = str(val)[:100]
        print(f"  - {k} ({val_type}): {val_desc}")
else:
    print("No dramas in results.")
