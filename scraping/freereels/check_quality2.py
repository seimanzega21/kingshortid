"""Check detail kualitas data - apakah deskripsi dan subtitle bahasa Indonesia?"""
import json, urllib.request

data   = json.loads(open('tab514_all_dramas.json', encoding='utf-8').read())
sample = list(data.values())[:5]

for v in sample:
    print(f"\n{'='*55}")
    print(f"Judul   : {v['title']}")
    print(f"Cover   : {v.get('cover', '(tidak ada)')[:80]}...")
    print(f"Deskripsi ({len(v.get('desc',''))} karakter):")
    print(f"  {v.get('desc','(kosong)')[:200]}")
    sub = v.get('ep1_sub_vtt', '')
    print(f"Subtitle: {'ADA - ' + sub[:70] if sub else '(tidak ada)'}")

# Cek apakah subtitle bisa diakses
print("\n\n--- Cek akses subtitle (3 sampel) ---")
tested = 0
for v in data.values():
    sub = v.get('ep1_sub_vtt', '')
    if not sub: continue
    try:
        req = urllib.request.Request(sub, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as f:
            content = f.read(200).decode('utf-8', errors='replace')
        print(f"[{v['title'][:35]}]")
        print(f"  URL: {sub[:60]}...")
        print(f"  Isi: {content[:150].strip()}")
        tested += 1
        if tested >= 3: break
    except Exception as e:
        print(f"  ERROR: {e}")
