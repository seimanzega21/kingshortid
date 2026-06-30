# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
}

target_dramas = [
    {'id': '18657', 'name': 'Maaf, Aku Hanya Dewa Pedang'},
    {'id': '18364', 'name': 'Mantan Kaya Terus Minta Balikan'},
    {'id': '19712', 'name': 'Cinta dan Peluru, Semua untuknya'},
    {'id': '16855', 'name': 'Dia Istri Sang Taipan'},
    {'id': '17871', 'name': 'Demi Anak, Aku Bangkit dari Kematian'},
    {'id': '19613', 'name': 'CEO Jatuh Cinta pada Ibu 6 Anak'},
    {'id': '18734', 'name': 'Sudah bilang, Aku Ibu Miliarder'},
    {'id': '18783', 'name': 'Rebut Kembali Takhta Dewa'},
    {'id': '19208', 'name': 'Sang Penagih Utang Takdir'},
    {'id': '19570', 'name': 'Salah Jurus? Tapi Aku Jadi Terkuat'},
    {'id': '8619',  'name': 'Mata Emas dari Jurang'}
]

action_id = '60ea10e5421e7d8bbba1e0d453714768474e2a8880'
results = []

for d in target_dramas:
    mid = d['id']
    url = f'https://vidrama.asia/en/watch/slug--{mid}/1?provider=stardusttv'
    hdrs = WEB_HDRS.copy()
    hdrs['next-action'] = action_id
    
    try:
        r = requests.post(url, headers=hdrs, data=json.dumps([mid, "id"]), timeout=15, verify=False)
        if r.ok:
            metadata = {}
            episodes = []
            
            # Parse Next.js action response lines
            for line in r.text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                try:
                    idx, content = line.split(':', 1)
                    obj = json.loads(content)
                    if isinstance(obj, dict) and 'title' in obj:
                        metadata = obj
                        if 'list' in obj and isinstance(obj['list'], list):
                            episodes = obj['list']
                except Exception:
                    pass
            
            if metadata:
                title = metadata.get('title')
                desc = metadata.get('description') or metadata.get('introduction') or ''
                cover = metadata.get('cover') or metadata.get('image') or ''
                total_eps = metadata.get('chapterCount') or len(episodes)
                
                print(f"ID: {mid} | Title: {title}")
                print(f"  Total Chapters: {total_eps}")
                print(f"  Episodes in 'list': {len(episodes)}")
                
                valid_eps = []
                for ep in episodes:
                    h264 = ep.get('_h264') or ep.get('videoUrl') or ep.get('url')
                    if h264:
                        valid_eps.append({
                            'episodeNumber': ep.get('episodeNumber') or ep.get('episodeNo'),
                            'url': h264
                        })
                
                print(f"  Valid H264 Links: {len(valid_eps)}")
                if valid_eps:
                    print(f"  First Ep URL: {valid_eps[0]['url'][-70:]}")
                print("-" * 50)
                
                results.append({
                    'id': mid,
                    'title': title,
                    'description': desc,
                    'cover': cover,
                    'totalEpisodes': total_eps,
                    'episodes': valid_eps
                })
        else:
            print(f"ID {mid} failed: {r.status_code}")
    except Exception as e:
        print(f"ID {mid} error: {e}")

# Save detailed results to JSON
with open('stardust_dramas_details.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
