"""
Fix remaining 11 dramas by matching episode count against 
the full DramaWave dubbed catalog. For dramas with unique ep counts,
we can match directly. For duplicates, use keyword similarity.
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

# Load pipeline status
status = json.loads(open(SCRIPT_DIR / 'pipeline_v2_status.json', 'r', encoding='utf-8').read())

# Get full info for unmatched dramas
unmatched = [
    ('Ayah Miliarder Menyamar Sulih', 58),
    ('Bertahan Hidup di Sekolah Elite(Sulih Suara)', 70),
    ('Bos Kuliah Lagi (Sulih Suara)', 87),
    ('Dari Medan Perang ke Istri CEO', 81),
    ('Ibu Kembali  Intrik Terbongkar', 60),
    ('Ikatan Terlarang (Sulih Suara)', 89),
    ('Meninggalkan Pewaris Miliarder', 66),
    ('Pacar Rahasiaku Ternyata Anak', 57),
    ('Pendekar yang Diremehkan Akhir', 77),
    ('Satu Insiden  Semua Pria Mengi', 79),
    ('Warisan Gunung Song (Sulih Suara)', 29),
]

# Get full titles
for i, (prefix, _) in enumerate(unmatched):
    for key, info in status.items():
        if isinstance(info, dict) and info.get('title', '').startswith(prefix[:12]):
            unmatched[i] = (prefix, _, info['title'])
            break
    if len(unmatched[i]) == 2:
        unmatched[i] = (prefix, _, prefix)

print(f"{'='*60}")
print(f"  Episode Count Matching — Full DramaWave Dubbed Catalog")
print(f"{'='*60}\n")

# Login and build full dubbed catalog with ep counts
client = DramaWaveClient(country='ID', language='id')
if not client.login():
    print("FAIL"); sys.exit(1)

series = json.loads(open(SCRIPT_DIR / 'freereels_series_ids.json', 'r', encoding='utf-8').read())
sids = [(k, v) for k, v in series.items() if isinstance(v, dict) and v.get('cover')]

# Build: ep_count → list of {sid, name, cover, desc}
ep_count_map = {}

print(f"  Building dubbed catalog from {len(sids)} series...")

for i, (sid, sdata) in enumerate(sids):
    info = client.get_drama_info(sid)
    if not info:
        continue
    
    tags = info.get('tag', [])
    ep_list = info.get('episode_list', [])
    has_id = any('id-ID' in ep.get('audio', []) for ep in ep_list[:1])
    
    if 'Dubbing' in tags or has_id:
        count = len(ep_list)
        meta = {
            'sid': sid,
            'name': info.get('name', sid),
            'cover': info.get('cover', sdata.get('cover', '')),
            'desc': info.get('desc', ''),
            'ep_count': count,
        }
        if count not in ep_count_map:
            ep_count_map[count] = []
        ep_count_map[count].append(meta)
    
    if (i+1) % 20 == 0:
        dubbed_total = sum(len(v) for v in ep_count_map.values())
        print(f"    [{i+1}/{len(sids)}] Dubbed: {dubbed_total}")
    
    time.sleep(0.25)

dubbed_total = sum(len(v) for v in ep_count_map.values())
print(f"\n  Total dubbed: {dubbed_total}")

# Print ep count distribution for debugging
print(f"\n  Episode count distribution:")
for count in sorted(ep_count_map.keys()):
    names = [m['name'][:30] for m in ep_count_map[count]]
    print(f"    {count:3d} eps: {len(ep_count_map[count])} dramas — {', '.join(names)}")

# Match unmatched dramas
print(f"\n  Matching unmatched dramas...")
matches = {}

for prefix, ep_count, full_title in unmatched:
    candidates = ep_count_map.get(ep_count, [])
    
    if len(candidates) == 1:
        # Unique match!
        matches[prefix] = candidates[0]
        matches[prefix]['full_title'] = full_title
        print(f"  ✅ {prefix[:30]:30s} ({ep_count} eps) = {candidates[0]['name'][:30]}")
    elif len(candidates) > 1:
        # Multiple candidates — use keyword similarity
        clean = re.sub(r'\(Sulih Suara\)', '', full_title).strip()
        clean = re.sub(r'Sulih Suara', '', clean).strip()
        words = set(w.lower() for w in clean.split() if len(w) > 2)
        
        # Try to translate title to English for matching
        en_title = translate_to_id(clean)  # Actually translate ID→EN for matching
        # Better: check which candidate's English name has overlapping meaning
        
        best = None
        best_score = 0
        for c in candidates:
            # Score based on keyword overlap with English name
            en_words = set(w.lower() for w in c['name'].split() if len(w) > 2)
            # Also check if episode count is exact
            score = 0
            if c['ep_count'] == ep_count:
                score += 10
            
            # Check if any Indonesian word appears in English title (cognates)
            for w in words:
                if w in c['name'].lower():
                    score += 5
            
            if score > best_score:
                best = c
                best_score = score
        
        if best:
            print(f"  ⚠️ {prefix[:30]:30s} ({ep_count} eps) → BEST: {best['name'][:30]} (score={best_score})")
            matches[prefix] = best
            matches[prefix]['full_title'] = full_title
        else:
            print(f"  ❌ {prefix[:30]:30s} ({ep_count} eps) → {len(candidates)} candidates, can't decide")
    else:
        print(f"  ❌ {prefix[:30]:30s} ({ep_count} eps) → No dubbed drama with this count")

print(f"\n  Matched: {len(matches)}/{len(unmatched)}")

# Update VPS
if matches:
    print(f"\n  Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)
    
    def run(sql):
        escaped = sql.replace("'", "'\\''")
        cmd = f"docker exec {DB_CONTAINER} psql -U supabase_admin -d postgres -t -A -c '{escaped}'"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
        return stdout.read().decode('utf-8', errors='replace').strip()
    
    updated = 0
    for vps_prefix, meta in matches.items():
        search = vps_prefix[:20].replace("'", "''")
        result = run(f"SELECT id, title, description FROM dramas WHERE title ILIKE '%{search}%' LIMIT 1")
        if not result or '|' not in result:
            print(f"  ❌ {vps_prefix[:30]} | Not in VPS")
            continue
        
        parts = result.split('|')
        drama_id = parts[0].strip()
        current_title = parts[1].strip()
        current_desc = parts[2].strip() if len(parts) > 2 else ''
        
        new_cover = meta['cover']
        en_desc = meta['desc']
        full_title = meta.get('full_title', vps_prefix)
        
        # Translate description
        id_desc = translate_to_id(en_desc) if en_desc else ''
        time.sleep(0.3)
        
        updates = []
        changes = []
        
        if full_title and len(full_title) > len(current_title):
            safe_title = full_title.replace("'", "''")
            updates.append(f"title = '{safe_title}'")
            changes.append("title")
        
        if new_cover:
            safe_cover = new_cover.replace("'", "''")
            updates.append(f"cover = '{safe_cover}'")
            updates.append(f"banner = '{safe_cover}'")
            changes.append("cover")
        
        if id_desc and (not current_desc or 'Drama pendek Indonesia' in current_desc or len(current_desc) < 30):
            safe_desc = id_desc.replace("'", "''")
            updates.append(f"description = '{safe_desc}'")
            changes.append("desc")
        
        if updates:
            sql = f"UPDATE dramas SET {', '.join(updates)} WHERE id = '{drama_id}'"
            run(sql)
            print(f"  ✅ {vps_prefix[:28]:28s} → {meta['name'][:22]} | {', '.join(changes)}")
            if id_desc:
                print(f"     📝 {id_desc[:70]}")
            updated += 1
    
    ssh.close()
    print(f"\n  Updated: {updated}")

print(f"\n{'='*60}")
