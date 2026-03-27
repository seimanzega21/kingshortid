"""
Final fix — Single pass approach:
1. Build full dubbed catalog (259 series → ~150 dubbed) — ONE pass
2. Match ALL VPS dramas by ep count
3. Translate + update ALL generic descriptions
4. Fix Warisan Gunung Song cover
"""
import json, sys, re, requests, paramiko, time
from pathlib import Path
paramiko.DSSKey = paramiko.RSAKey
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_CONTAINER = 'supabase-db-og8gwooogk480gcws0o84ssc'

SCRIPT_DIR = Path(__file__).parent
from freereels_scraper import DramaWaveClient

CACHED_CATALOG = SCRIPT_DIR / 'dubbed_metadata_cache.json'

def translate_to_id(text):
    if not text or len(text) < 5: return text
    try:
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client': 'gtx', 'sl': 'en', 'tl': 'id', 'dt': 't', 'q': text}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            result = r.json()
            return ''.join(part[0] for part in result[0] if part[0])
    except: pass
    return text

print(f"{'='*60}")
print(f"  Final Metadata Fix — Cached Catalog + Translation")
print(f"{'='*60}\n")

# Step 1: Build or load dubbed catalog
catalog = []

if CACHED_CATALOG.exists():
    catalog = json.loads(CACHED_CATALOG.read_text(encoding='utf-8'))
    print(f"  ✅ Loaded {len(catalog)} dubbed dramas from cache")
else:
    print(f"  Building dubbed catalog from DramaWave API...")
    client = DramaWaveClient(country='ID', language='id')
    if not client.login():
        print("FAIL"); sys.exit(1)
    
    series = json.loads(open(SCRIPT_DIR / 'freereels_series_ids.json', 'r', encoding='utf-8').read())
    sids = [(k, v) for k, v in series.items() if isinstance(v, dict) and v.get('cover')]
    
    for i, (sid, sdata) in enumerate(sids):
        info = client.get_drama_info(sid)
        if not info: continue
        
        tags = info.get('tag', [])
        ep_list = info.get('episode_list', [])
        has_id = any('id-ID' in ep.get('audio', []) for ep in ep_list[:1])
        
        if 'Dubbing' in tags or has_id:
            catalog.append({
                'sid': sid,
                'name': info.get('name', sid),
                'cover': info.get('cover', sdata.get('cover', '')),
                'desc': info.get('desc', ''),
                'ep_count': len(ep_list),
            })
        
        if (i+1) % 20 == 0:
            print(f"    [{i+1}/{len(sids)}] Dubbed: {len(catalog)}")
        time.sleep(0.25)
    
    # Save cache
    CACHED_CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  Saved {len(catalog)} dubbed dramas to cache")

# Build ep_count → entries
ep_map = {}
for entry in catalog:
    c = entry['ep_count']
    if c not in ep_map:
        ep_map[c] = []
    ep_map[c].append(entry)

# Step 2: Get VPS dramas
print(f"\n  Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)

def run(sql):
    escaped = sql.replace("'", "'\\''")
    cmd = f"docker exec {DB_CONTAINER} psql -U supabase_admin -d postgres -t -A -c '{escaped}'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    return stdout.read().decode('utf-8', errors='replace').strip()

result = run("""
    SELECT DISTINCT d.id, d.title, d.cover, d.description
    FROM dramas d
    INNER JOIN episodes e ON e.drama_id = d.id
    WHERE e.video_url LIKE '%freereels%'
    ORDER BY d.title
""")

# Load pipeline for episode counts
status = json.loads(open(SCRIPT_DIR / 'pipeline_v2_status.json', 'r', encoding='utf-8').read())

updated = 0
for line in result.split('\n'):
    if '|' not in line:
        continue
    parts = line.split('|')
    drama_id = parts[0].strip()
    title = parts[1].strip()
    cover = parts[2].strip() if len(parts) > 2 else ''
    desc = parts[3].strip() if len(parts) > 3 else ''
    
    # Check for issues
    is_generic = (
        'Drama Indonesia' in desc or 'Drama pendek' in desc or
        'Audio Indonesia' in desc or 'Drama Ikatan' in desc or
        '[FRkey:' in desc or len(desc) < 30
    )
    
    cover_broken = False
    if cover:
        try:
            r = requests.head(cover, timeout=3, allow_redirects=True)
            cover_broken = r.status_code != 200
        except:
            cover_broken = True
    else:
        cover_broken = True
    
    # Check if English/mixed description
    # "In my past life" text is English — also fix these
    has_english = desc.startswith('In my') or re.search(r'\b(the|and|with|her|his|from|into|but)\b', desc[:100])
    
    needs_fix = is_generic or cover_broken or has_english
    
    if not needs_fix:
        print(f"  ✅ {title[:40]:40s} | OK")
        continue
    
    issues = []
    if cover_broken: issues.append("cover")
    if is_generic: issues.append("generic desc")
    if has_english: issues.append("english desc")
    
    # Find episode count for matching
    ep_count = 0
    for key, info in status.items():
        if isinstance(info, dict) and info.get('title', '').startswith(title[:12]):
            parsed_file = SCRIPT_DIR / key
            if parsed_file.exists():
                parsed = json.loads(parsed_file.read_text(encoding='utf-8'))
                ep_count = len(parsed.get('episodes', []))
            break
    
    if ep_count == 0:
        print(f"  ❌ {title[:40]:40s} | {', '.join(issues)} — no ep count")
        continue
    
    candidates = ep_map.get(ep_count, [])
    if not candidates:
        print(f"  ❌ {title[:40]:40s} | {', '.join(issues)} — no {ep_count}-ep dubbed drama")
        continue
    
    # Use first candidate (for unique counts) or best match
    match = candidates[0]
    if len(candidates) > 1:
        # Try to narrow down (can't reliably, so just use first with desc)
        for c in candidates:
            if c['desc']:
                match = c
                break
    
    updates = []
    changes = []
    
    # Fix cover
    if cover_broken and match['cover']:
        try:
            r = requests.head(match['cover'], timeout=3, allow_redirects=True)
            if r.status_code == 200:
                safe_cover = match['cover'].replace("'", "''")
                updates.append(f"cover = '{safe_cover}'")
                updates.append(f"banner = '{safe_cover}'")
                changes.append("cover")
        except:
            pass
    
    # Fix description
    if (is_generic or has_english) and match['desc']:
        id_desc = translate_to_id(match['desc'])
        time.sleep(0.3)
        if id_desc and len(id_desc) > 20:
            safe_desc = id_desc.replace("'", "''")
            updates.append(f"description = '{safe_desc}'")
            changes.append("desc")
            print(f"  🔧 {title[:35]:35s} → {match['name'][:22]} | {', '.join(changes)}")
            print(f"     📝 {id_desc[:70]}")
        else:
            print(f"  ⚠️ {title[:35]:35s} | Translation failed")
    else:
        if changes:
            print(f"  🔧 {title[:35]:35s} → | {', '.join(changes)}")
    
    if updates:
        sql = f"UPDATE dramas SET {', '.join(updates)} WHERE id = '{drama_id}'"
        run(sql)
        updated += 1

ssh.close()

print(f"\n{'='*60}")
print(f"  Updated: {updated}")
print(f"{'='*60}")
