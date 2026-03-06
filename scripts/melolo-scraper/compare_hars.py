#!/usr/bin/env python3
"""Test: count series in all 3 HARs using the UPDATED extraction logic"""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def count_series_v2(har_path):
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    series = {}
    for entry in har['log']['entries']:
        url = entry['request']['url']
        if 'video_detail' not in url or 'video_model' in url:
            continue
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        try:
            data = json.loads(text)
        except:
            continue
        if not isinstance(data.get('data'), dict):
            continue
        
        d = data['data']
        video_datas = []
        
        if 'video_data' in d and isinstance(d['video_data'], dict):
            vd = d['video_data']
            sid = str(vd.get('series_id', '') or vd.get('series_id_str', ''))
            if sid and vd.get('video_list'):
                video_datas.append((sid, vd))
        else:
            for k, v in d.items():
                if not isinstance(v, dict):
                    continue
                vd = v.get('video_data')
                if not isinstance(vd, dict) or not vd.get('video_list'):
                    continue
                video_datas.append((k, vd))
        
        for sid, vd in video_datas:
            title = vd.get('series_title', '') or vd.get('book_name', '')
            eps = vd.get('total_episode', 0) or vd.get('episode_cnt', 0) or len(vd.get('video_list', []))
            abstract = vd.get('series_intro', '') or vd.get('abstract', '')
            
            if sid not in series or len(vd.get('video_list', [])) > len(series[sid].get('vids', [])):
                series[sid] = {
                    'title': title,
                    'eps': eps,
                    'vids': vd.get('video_list', []),
                    'abstract': abstract[:60] if abstract else '',
                }
    
    return series

for har_name in ['melolo1.har', 'melolo2.har', 'melolo3.har']:
    s = count_series_v2(har_name)
    print(f"\n{har_name}: {len(s)} series")
    for sid, info in sorted(s.items(), key=lambda x: -x[1]['eps'])[:10]:
        t = info['title'] or f"(no title {sid[-8:]})"
        print(f"  {t[:45]:<47} {info['eps']:>3} eps  {len(info['vids'])} vids")

# Combined unique
s1 = count_series_v2('melolo1.har')
s2 = count_series_v2('melolo2.har')
s3 = count_series_v2('melolo3.har')
all_ids = set(s1) | set(s2) | set(s3)
overlap_12 = set(s1) & set(s2)
overlap_13 = set(s1) & set(s3)
overlap_23 = set(s2) & set(s3)
new_in_2 = set(s2) - set(s1) - set(s3)
new_in_3 = set(s3) - set(s1) - set(s2)

print(f"\n=== SUMMARY ===")
print(f"melolo1: {len(s1)} | melolo2: {len(s2)} | melolo3: {len(s3)}")
print(f"Overlap 1∩2: {len(overlap_12)} | 1∩3: {len(overlap_13)} | 2∩3: {len(overlap_23)}")
print(f"New in melolo2: {len(new_in_2)} | New in melolo3: {len(new_in_3)}")
print(f"Total unique: {len(all_ids)}")

if new_in_2:
    print(f"\nNew in melolo2:")
    for sid in new_in_2:
        print(f"  {s2[sid]['title']}")
if new_in_3:
    print(f"\nNew in melolo3:")
    for sid in new_in_3:
        print(f"  {s3[sid]['title']}")
