import requests, boto3, re, urllib3
from botocore.config import Config

urllib3.disable_warnings()

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                    config=Config(signature_version='s3v4'), region_name='auto')

DRAMAS = [
    {'no': 1, 'title': 'Berhenti Berjudi, Utamakan Keluarga', 'db_id': 'r22zs10yvkmoq0vqn5sxofqz'},
    {'no': 2, 'title': 'Sang Pewaris Jawara Pedang Pertama', 'db_id': None, 'vidrama_search': True},
    {'no': 3, 'title': 'Romantis di Musim Dingin', 'db_id': None, 'vidrama_search': True},
    {'no': 4, 'title': '(Sulih suara) Pengemis Itu Sangat Berkuasa', 'db_id': None, 'vidrama_search': True},
    {'no': 5, 'title': 'Saat Aku Murka, Dunia Berguncang', 'db_id': None, 'vidrama_search': True},
]

def get_r2_counts(prefix):
    mp4 = vtt = 0
    try:
        resp = r2.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix, MaxKeys=1000)
        for c in resp.get('Contents', []):
            if c['Key'].endswith('.mp4') and '_540p' not in c['Key']: mp4 += 1
            elif c['Key'].endswith('.vtt'): vtt += 1
    except: pass
    return mp4, vtt

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

# Search all in Vidrama
print('=== MENCARI SEMUA DI VIDRAMA ===')
vidrama_map = {}
for page in range(1, 20):
    url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if r.ok:
            items = r.json().get('data', [])
            if not items: break
            for it in items:
                title = it.get('title', '').lower()
                for d in DRAMAS:
                    if d.get('vidrama_search'):
                        search_title = d['title'].lower().replace('(sulih suara)', '').strip()
                        if search_title in title or title in search_title:
                            if d['no'] not in vidrama_map:
                                vidrama_map[d['no']] = {'id': it.get('id'), 'title': it.get('title'), 'total': it.get('totalEpisodes')}
    except: pass

for k, v in vidrama_map.items():
    print(f"  #{k}: {v['title']} | ID: {v['id']} | Eps: {v['total']}")

print()
print('=== CEK DATABASE & R2 ===')
for d in DRAMAS:
    print(f"\n#{d['no']} — {d['title']}")
    
    # Check DB
    db_id = d.get('db_id')
    if not db_id:
        # Search by title
        r = requests.get(f"{API_BASE}/api/dramas?limit=1000", headers=ADMIN_HDR, timeout=30)
        if r.ok:
            for drama in r.json().get('dramas', []):
                if d['title'].lower() in drama.get('title','').lower() or drama.get('title','').lower() in d['title'].lower():
                    db_id = drama.get('id')
                    print(f"  DB ID: {db_id}")
                    break
    
    if db_id:
        ep_r = requests.get(f"{API_BASE}/api/dramas/{db_id}/episodes", headers=ADMIN_HDR, timeout=20)
        if ep_r.ok:
            data = ep_r.json()
            eps = data if isinstance(data, list) else data.get('episodes', [])
            print(f"  Episodes in DB: {len(eps)}")
    else:
        print(f"  NOT IN DB")
    
    # Check R2
    prefix = f"netshortv2/{slugify(d['title'])}/"
    mp4, vtt = get_r2_counts(prefix)
    print(f"  R2: {mp4} video, {vtt} subtitle")
    
    # Vidrama info
    if d['no'] in vidrama_map:
        v = vidrama_map[d['no']]
        print(f"  Vidrama: {v['title']} | ID: {v['id']} | Total: {v['total']}")
