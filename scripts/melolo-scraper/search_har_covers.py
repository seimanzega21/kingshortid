"""Search all HAR response bodies for covers by matching drama titles"""
import json, os, re

har_files = ['melolo1.har', 'melolo2.har', 'melolo3.har', 'melolo4.har']

# Search by title keywords (Indonesian)
target_slugs = {
    'Setelah Bertapa': 'setelah-bertapa-kutaklukkan-dunia',
    'Membicarakan Kaisar': 'siapa-yang-sedang-membicarakan-kaisar',
    'Perubah Nasib': 'sistem-perubah-nasib',
    'Suami Sultan': 'sistem-suami-sultan',
    '1977': 'tahun-1977-penuh-peluang',
}

# Also search Chinese titles that might be in the original data
cn_keywords = {
    'bertapa': ['修炼', '闭关', '出山'],
    'kaisar': ['皇帝', '谁在议论'],
    'nasib': ['系统', '改命', '逆天'],
    'sultan': ['系统', '富豪', '老公'],
    '1977': ['1977', '机遇'],
}

found_covers = {}

for har_file in har_files:
    if not os.path.exists(har_file):
        continue
    
    print(f"\nSearching {har_file}...")
    
    with open(har_file, 'r', encoding='utf-8', errors='replace') as f:
        data = json.load(f)
    
    entries = data.get('log', {}).get('entries', [])
    
    for entry in entries:
        text = entry.get('response', {}).get('content', {}).get('text', '')
        mime = entry.get('response', {}).get('content', {}).get('mimeType', '')
        
        if not text or 'json' not in mime:
            continue
        
        # Search for each target title
        for keyword, slug in target_slugs.items():
            if keyword.lower() in text.lower():
                try:
                    rdata = json.loads(text)
                    rtext = text
                    
                    # Find the keyword position and extract nearby cover URL
                    idx = rtext.lower().find(keyword.lower())
                    if idx >= 0:
                        # Get context around the match (2000 chars each side)
                        context = rtext[max(0, idx-2000):idx+2000]
                        covers = re.findall(r'(https?://[^"\\]+(?:\.jpg|\.jpeg|\.png|\.webp|\.heic)[^"\\]*)', context)
                        
                        if covers:
                            url = entry.get('request', {}).get('url', '')[:80]
                            print(f"\n  🎯 Found '{keyword}' in API: {url}")
                            for c in covers[:3]:
                                c_clean = c.replace('\\u0026', '&')
                                print(f"    📸 {c_clean[:120]}")
                                if slug not in found_covers:
                                    found_covers[slug] = c_clean
                except:
                    pass

print(f"\n\n{'='*60}")
print("RESULTS")
print('='*60)

for slug in target_slugs.values():
    if slug in found_covers:
        print(f"\n✅ {slug}")
        print(f"   {found_covers[slug][:120]}")
    else:
        print(f"\n❌ {slug}: NOT FOUND in HAR files")

# Save results
with open('found_covers.json', 'w') as f:
    json.dump(found_covers, f, indent=2)

print(f"\nSaved {len(found_covers)} covers to found_covers.json")
