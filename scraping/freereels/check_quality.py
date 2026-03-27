"""Check kualitas data drama Indonesia dari tab 514"""
import json

data = json.loads(open('tab514_all_dramas.json', encoding='utf-8').read())

total = len(data)
has_cover   = sum(1 for v in data.values() if v.get('cover'))
has_desc    = sum(1 for v in data.values() if v.get('desc') and len(v['desc']) > 10)
has_sub_id  = sum(1 for v in data.values() if v.get('ep1_sub_vtt'))
has_hls     = sum(1 for v in data.values() if v.get('ep1_hls'))

print(f"Total dramas      : {total}")
print(f"Ada cover         : {has_cover} ({100*has_cover//total}%)")
print(f"Ada deskripsi     : {has_desc} ({100*has_desc//total}%)")
print(f"Ada subtitle ID   : {has_sub_id} ({100*has_sub_id//total}%)")
print(f"Ada HLS (audio ID): {has_hls} ({100*has_hls//total}%)")

print("\n--- Sample 5 drama ---")
for k, v in list(data.items())[:5]:
    sub  = v.get('ep1_sub_vtt', '')[:60] + '...' if v.get('ep1_sub_vtt') else '(tidak ada)'
    desc = v.get('desc', '')[:80] + '...' if v.get('desc') else '(tidak ada)'
    cover = 'ADA' if v.get('cover') else '(tidak ada)'
    print(f"\n[{v['title'][:45]}]")
    print(f"  Cover   : {cover}")
    print(f"  Deskripsi: {desc}")
    print(f"  Subtitle: {sub}")
