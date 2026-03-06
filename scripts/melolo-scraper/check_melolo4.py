#!/usr/bin/env python3
"""Quick analysis of melolo4.har"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo4.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']
print(f'melolo4.har: {len(entries)} entries')

series = {}
for entry in entries:
    url = entry['request']['url']
    if 'video_detail' not in url or 'video_model' in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text: continue
    try: data = json.loads(text)
    except: continue
    if not isinstance(data.get('data'), dict): continue
    d = data['data']
    vds = []
    if 'video_data' in d and isinstance(d['video_data'], dict):
        vd = d['video_data']
        sid = str(vd.get('series_id', '') or vd.get('series_id_str', ''))
        if sid and vd.get('video_list'): vds.append((sid, vd))
    else:
        for k, v in d.items():
            if isinstance(v, dict):
                vd = v.get('video_data')
                if isinstance(vd, dict) and vd.get('video_list'): vds.append((k, vd))
    for sid, vd in vds:
        title = vd.get('series_title', '') or vd.get('book_name', '')
        eps = vd.get('total_episode', 0) or vd.get('episode_cnt', 0) or len(vd.get('video_list', []))
        vids = len(vd.get('video_list', []))
        cover = 'Y' if vd.get('series_cover') else 'N'
        if sid not in series or vids > series[sid]['vids']:
            series[sid] = {'title': title, 'eps': eps, 'vids': vids, 'cover': cover}

print(f'Series found: {len(series)}\n')
for sid, info in sorted(series.items(), key=lambda x: -x[1]['eps']):
    t = info['title'] or f"(no title {sid[-8:]})"
    print(f"  {t[:50]:52s} {info['eps']:3d} eps  {info['vids']} vids  Cover:{info['cover']}")

# Check overlap with other HARs
prev_ids = set()
for h in ['melolo1.har', 'melolo2.har', 'melolo3.har']:
    try:
        with open(h, 'r', encoding='utf-8') as f: hd = json.load(f)
        for e in hd['log']['entries']:
            u = e['request']['url']
            if 'video_detail' not in u or 'video_model' in u: continue
            t = e['response']['content'].get('text', '')
            if not t: continue
            try: dd = json.loads(t)
            except: continue
            if not isinstance(dd.get('data'), dict): continue
            dx = dd['data']
            if 'video_data' in dx and isinstance(dx['video_data'], dict):
                vx = dx['video_data']
                sx = str(vx.get('series_id', '') or vx.get('series_id_str', ''))
                if sx and vx.get('video_list'): prev_ids.add(sx)
            else:
                for k, v in dx.items():
                    if isinstance(v, dict) and isinstance(v.get('video_data'), dict) and v['video_data'].get('video_list'):
                        prev_ids.add(k)
    except: pass

new = set(series.keys()) - prev_ids
overlap = set(series.keys()) & prev_ids
print(f'\n=== OVERLAP ===')
print(f'Total in melolo4: {len(series)}')
print(f'Already in melolo1-3: {len(overlap)}')
print(f'NEW dramas: {len(new)}')
if new:
    print(f'\nNew dramas in melolo4:')
    for sid in sorted(new, key=lambda x: -series[x]['eps']):
        print(f"  {series[sid]['title']} ({series[sid]['eps']} eps, {series[sid]['vids']} vids)")
if overlap:
    print(f'\nOverlapping:')
    for sid in sorted(overlap, key=lambda x: -series[x]['eps']):
        print(f"  {series[sid]['title']} ({series[sid]['eps']} eps)")
