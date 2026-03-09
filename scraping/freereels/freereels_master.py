"""
FreeReels Indonesian Dubbed Drama Scraper — MASTER PIPELINE
============================================================
CONFIRMED WORKING (2026-03-09):
  - Login: POST /anonymous/login (plain JSON + Skip-Encrypt:1) 
  - Tab 514 feed: POST /homepage/v2/tab/feed PLAIN JSON
    Body: {tab_key:'514', module_key:'514', page:N, page_size:20}
    Headers: app-name=com.freereels.app, device=android
  - Series key field: items[].key (NOT id!)
  - Drama info: GET /drama/info?series_id=[KEY]  
  - Indonesian dubbed: episode.external_audio_h264_m3u8
  - CDN: video-v6.mydramawave.com, static-v1.mydramawave.com

PIPELINE:
  1. Paginate tab 514 (Dubbed) → collect series keys
  2. GET drama/info per series_id → episode list
  3. Download HLS → ffmpeg H264 CRF28 faststart MP4
  4. Upload to R2: freereels/{folder}/ep_NNN.mp4
  5. DB import as isActive=False (pending)

Usage:
  python freereels_master.py --collect --limit 250    # Step 1: collect IDs
  python freereels_master.py --download --limit 200   # Step 2-4: download + R2
  python freereels_master.py --import-db              # Step 5: DB import
  python freereels_master.py --all --limit 200        # Full pipeline
"""
import sys, json, time, os, re, base64, hashlib, subprocess, urllib.request, argparse
import requests, psycopg2
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3; from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
APP_SECRET  = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY     = b'2r36789f45q01ae5'
FR_BASE     = 'https://apiv2.free-reels.com/frv2-api'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
SERIES_IDS_FILE = Path('freereels_series_ids.json')
TEMP_DIR        = Path(os.environ.get('TEMP', '/tmp')) / 'fr_dl'
TEMP_DIR.mkdir(exist_ok=True)

# ffmpeg: H264 CRF28 baseline, 720p max, faststart
FFMPEG_OPTS = ['-c:v','libx264','-crf','28','-preset','fast',
               '-profile:v','baseline','-level','3.1',
               '-c:a','aac','-b:a','96k','-ar','44100',
               '-vf','scale=-2:min(720\,ih)',
               '-movflags','faststart','-y']

GENRES_MAP = {
    'Drama':'Drama','Romance':'Romance','Romantis':'Romance',
    'Bisnis':'Business','Aksi':'Action','Komedi':'Comedy',
    'Thriller':'Thriller','Misteri':'Mystery','Fantasi':'Fantasy',
    'Sejarah':'Historical','Kampus':'School','Keluarga':'Family',
    'Balas Dendam':'Revenge','Kontemporer':'Contemporary',
}

# ── AES + Auth ────────────────────────────────────────────────────────────────
def enc(d):
    p = json.dumps(d, separators=(',',':')).encode()
    pad = 16-(len(p)%16); p += bytes([pad]*pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor()
    return base64.b64encode(iv+e.update(p)+e.finalize()).decode()

def dec(t):
    try:
        r = base64.b64decode(t); iv,ct = r[:16],r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct)+c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

# ── FreeReels Client ──────────────────────────────────────────────────────────
class FRClient:
    def __init__(self):
        self.dh  = hashlib.md5(b'freereels_master_pipeline_v1').hexdigest()
        self.ak  = self.ase = None
        self.sess = requests.Session()
        self.sess.headers.update({
            'app-name':'com.freereels.app', 'device':'android',
            'app-version':'2.2.10', 'device-id':self.dh, 'device-hash':self.dh,
            'country':'ID', 'language':'id', 'shortcode':'id',
            'User-Agent':'okhttp/4.12.0',
        })

    def login(self):
        # Priority 1: Use saved Google account token (all episodes accessible)
        token_file = Path('fr_vip_token.json')
        if token_file.exists():
            try:
                t = json.loads(token_file.read_text(encoding='utf-8'))
                self.ak  = t.get('auth_key', '')
                self.ase = t.get('auth_secret', '')
                if self.ak and self.ase:
                    print(f'[AUTH] Google account: {t.get("nickname","?")} (key={self.ak[:8]}...)')
                    return True
            except: pass

        # Fallback: Anonymous login (limited to ~10 free eps per drama)
        r = self.sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': self.dh},
                           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
        d = (r.json() if r.ok else {}).get('data', {})
        self.ak = d.get('auth_key', ''); self.ase = d.get('auth_secret', '')
        ok = bool(self.ak)
        print(f'[AUTH] Anonymous {"OK key="+self.ak[:8]+"..." if ok else "FAILED"}')
        return ok


    def _ah(self):
        sig = hashlib.md5(f'{APP_SECRET}&{self.ase}'.encode()).hexdigest()
        return {'authorization': f'oauth_signature={sig},oauth_token={self.ak},ts={int(time.time()*1000)}'}

    def tab_feed(self, page=1, page_size=20):
        """Get dubbed dramas from tab 514. PLAIN JSON required."""
        r = self.sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
                           json={'tab_key':'514','module_key':'514','page':page,'page_size':page_size},
                           headers={**self._ah(),'Content-Type':'application/json','Skip-Encrypt':'1'}, timeout=15)
        resp = r.json() if r.ok else {}
        if resp.get('code') in [200, 0]:
            data = resp.get('data', {})
            items = data.get('items') or data.get('list', [])
            return items
        return []

    def drama_info(self, series_id):
        """GET /drama/info?series_id=KEY - returns info+episode_list."""
        r = self.sess.get(f'{FR_BASE}/drama/info', headers=self._ah(),
                          params={'series_id': series_id}, timeout=20)
        resp = dec(r.text) or r.json() if r.ok else {}
        if resp.get('code') not in [200, 0]: return None
        data = resp.get('data', {})
        return data.get('info', data) if isinstance(data, dict) else None

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2c, key):
    try: r2c.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload_file(r2c, path, key, ct='video/mp4'):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key, ExtraArgs={'ContentType':ct},
                           Config=boto3.s3.transfer.TransferConfig(multipart_threshold=50*1024*1024))
    return f'{R2_PUBLIC}/{key}'

def r2_upload_bytes(r2c, data, key, ct='application/json'):
    r2c.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=ct)
    return f'{R2_PUBLIC}/{key}'

def r2_list_meta_files(r2c):
    files, token = [], None
    while True:
        kw = {'Bucket':R2_BUCKET,'Prefix':'freereels/','MaxKeys':1000}
        if token: kw['ContinuationToken'] = token
        resp = r2c.list_objects_v2(**kw)
        files += [o['Key'] for o in resp.get('Contents',[]) if o['Key'].endswith('/metadata.json')]
        token = resp.get('NextContinuationToken')
        if not token: break
    return files

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_folder(title):
    s = re.sub(r'\((?:Sulih Suara|Doblaje|Dubbed?)\)', '', title, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:50] or 'drama'

def has_indo_audio(ep):
    return 'id-ID' in ep.get('audio', []) or bool(ep.get('external_audio_h264_m3u8',''))

def get_sub_vtt(ep):
    for s in (ep.get('subtitle_list') or []):
        if s.get('language') == 'id-ID':
            return s.get('vtt','') or s.get('subtitle','')
    return ''

def dl_bytes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as f: return f.read()
    except: return None

def ffmpeg_convert(hls_url, out_mp4):
    """HLS → H264 CRF28 faststart MP4."""
    if not hls_url: return False, 'no URL'
    cmd = ['ffmpeg', '-i', hls_url, *FFMPEG_OPTS, str(out_mp4)]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=300, encoding='utf-8', errors='replace')
        if res.returncode != 0:
            # Fallback: stream copy
            cmd2 = ['ffmpeg', '-i', hls_url, '-c','copy', '-movflags','faststart', '-y', str(out_mp4)]
            res2 = subprocess.run(cmd2, capture_output=True, timeout=300, encoding='utf-8', errors='replace')
            if res2.returncode != 0:
                return False, res.stderr[-200:]
        if not out_mp4.exists() or out_mp4.stat().st_size < 5000: return False, 'too small'
        return True, f'{out_mp4.stat().st_size//1024}KB'
    except subprocess.TimeoutExpired: return False, 'timeout'
    except Exception as e: return False, str(e)

def map_genres(genres):
    return [GENRES_MAP.get(g, g) for g in genres] or ['Drama','Romance']

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: Collect series IDs from tab 514
# ══════════════════════════════════════════════════════════════════════════════
def stage_collect(client, target=250):
    existing = {}
    if SERIES_IDS_FILE.exists():
        with open(SERIES_IDS_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    print(f'Existing: {len(existing)} series')
    
    page = 1
    while len(existing) < target:
        items = client.tab_feed(page=page, page_size=20)
        if not items:
            print(f'No more items at page {page}. Total: {len(existing)}')
            break
        
        new = 0
        for item in items:
            key = item.get('key') or item.get('id') or item.get('series_id')
            if not key or key in existing: continue
            existing[str(key)] = {
                'series_id': str(key),
                'title': item.get('name', str(key)),
                'cover': item.get('cover', ''),
                'episodes': item.get('episode_count', 0),
                'tags': item.get('tag', []),
                'genres': item.get('series_tag', []),
            }
            new += 1
        
        print(f'  Page {page}: +{new} new (total: {len(existing)})')
        if not new: break
        page += 1
        time.sleep(0.5)
        
        # Re-auth every 20 pages
        if page % 20 == 0: client.login()
    
    with open(SERIES_IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f'\n✓ Collected {len(existing)} FreeReels dubbed dramas → {SERIES_IDS_FILE}')
    return existing

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2-4: Download episodes → R2
# ══════════════════════════════════════════════════════════════════════════════
def stage_download(client, r2c, series_map, limit=None):
    items = list(series_map.items())
    if limit: items = items[:limit]
    ok = skip = fail = 0
    
    for i, (sid, meta) in enumerate(items, 1):
        print(f'\n[{i}/{len(items)}] {sid} — {meta.get("title","")[:40]}')
        
        info = client.drama_info(sid)
        if not info:
            print(f'  SKIP: cannot fetch info'); skip += 1; continue

        ep_list = info.get('episode_list', [])
        indo_eps = [ep for ep in ep_list if has_indo_audio(ep)]
        if not indo_eps:
            print(f'  SKIP: no Indonesian audio'); skip += 1; continue
        
        title  = info.get('name', meta.get('title', sid))
        folder = safe_folder(title)
        prefix = f'freereels/{folder}'
        meta_key = f'{prefix}/metadata.json'
        
        # Upload cover
        cover_key = f'{prefix}/cover.jpg'
        cover_r2  = f'{R2_PUBLIC}/{cover_key}'
        if not r2_exists(r2c, cover_key):
            img = dl_bytes(info.get('cover', meta.get('cover', '')))
            if img: r2_upload_bytes(r2c, img, cover_key, 'image/jpeg')
        
        ep_results = []
        uploaded = 0
        
        for j, ep in enumerate(indo_eps, 1):
            ep_num = ep.get('index', j)
            hls    = ep.get('external_audio_h264_m3u8','') or ep.get('m3u8_url','')
            dur    = ep.get('duration', 0)
            sub    = get_sub_vtt(ep)
            
            mp4_key = f'{prefix}/ep_{ep_num:03d}.mp4'
            
            video_url   = f'{R2_PUBLIC}/{mp4_key}'
            uploaded_ep = False
            
            if r2_exists(r2c, mp4_key):
                print(f'  [{j:03d}/{len(indo_eps)}] ep{ep_num:03d} — already in R2')
                uploaded_ep = True
            elif hls:
                out = TEMP_DIR / f'{folder}_ep{ep_num:03d}.mp4'
                ok2, msg = ffmpeg_convert(hls, out)
                if ok2:
                    r2_upload_file(r2c, out, mp4_key, 'video/mp4')
                    size = out.stat().st_size/1024/1024
                    print(f'  [{j:03d}/{len(indo_eps)}] ep{ep_num:03d} ✓ {size:.1f}MB → R2')
                    uploaded_ep = True
                    try: out.unlink()
                    except: pass
                else:
                    print(f'  [{j:03d}/{len(indo_eps)}] ep{ep_num:03d} ✗ {msg}')
            else:
                print(f'  [{j:03d}/{len(indo_eps)}] ep{ep_num:03d} — no HLS (locked)')
            
            if uploaded_ep: uploaded += 1
            ep_results.append({
                'episode': ep_num, 'duration': dur,
                'videoUrl': video_url if uploaded_ep else '',
                'subtitleVtt': sub, 'uploaded': uploaded_ep,
                'free': ep.get('video_type') == 'free',
            })
            time.sleep(0.3)
        
        # Save metadata to R2
        metadata = {
            'source': 'freereels_dubbed', 'series_id': sid,
            'title': title,
            'titleClean': re.sub(r'\((?:Sulih Suara|Doblaje|Dubbed?)\)', '', title, flags=re.IGNORECASE).strip(),
            'description': info.get('desc', ''),
            'cover': cover_r2,
            'genres': map_genres(info.get('series_tag', meta.get('genres', []))),
            'tags': info.get('tag', meta.get('tags', [])),
            'content_tags': info.get('content_tags', []),
            'totalEpisodes': len(indo_eps),
            'uploadedEpisodes': uploaded,
            'status': 'completed' if info.get('finish_status') == 2 else 'ongoing',
            'language': 'Indonesia', 'audioLanguage': 'id-ID', 'country': 'China',
            'viewCount': info.get('view_count', 0),
            'r2Folder': prefix,
            'episodes': ep_results,
            'scrapedAt': int(time.time()),
        }
        r2_upload_bytes(r2c, json.dumps(metadata, ensure_ascii=False, indent=2).encode(), meta_key)
        print(f'  Metadata → R2 ✓ ({uploaded}/{len(indo_eps)} eps uploaded)')
        
        if uploaded > 0: ok += 1
        else: skip += 1
        
        # Re-auth every 20 dramas
        if i % 20 == 0: client.login()
        time.sleep(1)
    
    print(f'\n{"="*50}')
    print(f'✓ OK:{ok}  ⊘ Skip:{skip}  ✗ Fail:{fail}')

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5: DB Import as isActive=False
# ══════════════════════════════════════════════════════════════════════════════
def stage_import_db(r2c, dry_run=False):
    meta_files = r2_list_meta_files(r2c)
    print(f'Found {len(meta_files)} drama metadata files in R2')
    
    conn = None if dry_run else psycopg2.connect(DATABASE_URL)
    if conn: conn.autocommit = False
    cur = conn.cursor() if conn else None
    
    dramas_ok = eps_ok = subs_ok = skip = fail = 0

    for i, mkey in enumerate(meta_files, 1):
        obj = r2c.get_object(Bucket=R2_BUCKET, Key=mkey)
        meta = json.loads(obj['Body'].read().decode('utf-8'))
        
        sid   = meta.get('series_id','')
        title = meta.get('titleClean') or meta.get('title','?')
        eps   = [e for e in meta.get('episodes',[]) if e.get('uploaded') and e.get('videoUrl')]
        
        print(f'[{i:03d}] {title[:45]} ({len(eps)} eps)')
        if not eps: skip += 1; continue
        if dry_run: dramas_ok +=1; continue
        
        try:
            # Check existing
            cur.execute("SELECT id FROM \"Drama\" WHERE description LIKE %s LIMIT 1",
                       (f'%[FRid:{sid}]%',))
            row = cur.fetchone()
            
            if row:
                drama_id = row[0]
            else:
                desc = (meta.get('description','') or 'Drama pendek bahasa Indonesia.') + f'\n[FRid:{sid}]'
                cur.execute("""
                    INSERT INTO "Drama" (
                        id,title,description,cover,banner,
                        genres,"tagList","totalEpisodes",
                        rating,views,likes,"reviewCount","averageRating",
                        status,"isVip","isFeatured","isActive","ageRating",
                        country,language,"createdAt","updatedAt"
                    ) VALUES (
                        gen_random_uuid(),%s,%s,%s,%s,
                        %s::text[],%s::text[],%s,
                        0,%s,0,0,0,
                        %s,false,false,false,'all',
                        %s,%s,NOW(),NOW()
                    ) RETURNING id
                """, (
                    title, desc, meta.get('cover',''), meta.get('cover',''),
                    meta.get('genres',['Drama']),
                    meta.get('tags',[]) + meta.get('content_tags',[]),
                    len(eps), meta.get('viewCount',0),
                    meta.get('status','ongoing'),
                    meta.get('country','China'), meta.get('language','Indonesia'),
                ))
                drama_id = cur.fetchone()[0]
                dramas_ok += 1

            for ep in eps:
                ep_num = ep.get('episode', 0)
                cur.execute("SELECT id FROM \"Episode\" WHERE \"dramaId\"=%s AND \"episodeNumber\"=%s",
                           (drama_id, ep_num))
                if cur.fetchone(): continue
                cur.execute("""
                    INSERT INTO "Episode" (
                        id,"dramaId","episodeNumber",title,description,
                        thumbnail,"videoUrl",duration,
                        "isVip","coinPrice",views,"isActive","releaseDate",
                        "createdAt","updatedAt"
                    ) VALUES (
                        gen_random_uuid(),%s,%s,%s,'',
                        %s,%s,%s,
                        false,0,0,false,NOW(),
                        NOW(),NOW()
                    ) RETURNING id
                """, (drama_id, ep_num, f'Episode {ep_num}',
                      ep.get('thumbnail',''), ep.get('videoUrl',''), ep.get('duration',0)))
                ep_id = cur.fetchone()[0]
                eps_ok += 1
                
                sub = ep.get('subtitleVtt','')
                if sub:
                    cur.execute("SELECT id FROM \"Subtitle\" WHERE \"episodeId\"=%s AND language='id' LIMIT 1", (ep_id,))
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO "Subtitle" (id,"episodeId",language,label,url,"isDefault","createdAt")
                            VALUES (gen_random_uuid(),%s,'id','Bahasa Indonesia',%s,true,NOW())
                        """, (ep_id, sub))
                        subs_ok += 1
            
            conn.commit()
        except Exception as e:
            if conn: conn.rollback()
            print(f'  ERROR: {e}'); fail += 1

    print(f'\n{"="*50}')
    print(f'✓ Dramas: {dramas_ok}  Episodes: {eps_ok}  Subs: {subs_ok}')
    print(f'⊘ Skipped: {skip}  ✗ Failed: {fail}')
    print(f'\n⚠️  All imported with isActive=False — activate in admin to publish!')
    if conn: cur.close(); conn.close()

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description='FreeReels Dubbed Drama Master Pipeline')
    p.add_argument('--collect',    action='store_true', help='Stage 1: collect series IDs from tab 514')
    p.add_argument('--download',   action='store_true', help='Stage 2-4: download episodes → R2')
    p.add_argument('--import-db',  action='store_true', help='Stage 5: import to DB as pending', dest='import_db')
    p.add_argument('--all',        action='store_true', help='Run all stages')
    p.add_argument('--limit',      type=int, default=250, help='Max dramas (default: 250)')
    p.add_argument('--dry-run',    action='store_true', help='No R2/DB writes')
    a = p.parse_args()
    
    if not any([a.collect, a.download, a.import_db, a.all]):
        p.print_help(); return

    print('═'*55)
    print('  FreeReels Indonesian Dubbed — Master Pipeline')
    print('═'*55)
    print(f'  Mode: {"DRY-RUN" if a.dry_run else "PRODUCTION"}  Limit: {a.limit}')

    client = FRClient()
    if not client.login(): sys.exit(1)

    r2c = None if a.dry_run else get_r2()

    SEP = '═' * 55
    if a.collect or a.all:
        print(f'\n{SEP}')
        print(f'  STAGE 1: Collecting Series IDs from Tab 514')
        print(SEP)
        series_map = stage_collect(client, target=a.limit)
    elif a.download or a.import_db:
        if not SERIES_IDS_FILE.exists():
            print(f'ERROR: {SERIES_IDS_FILE} not found. Run --collect first.'); sys.exit(1)
        with open(SERIES_IDS_FILE, encoding='utf-8') as f:
            series_map = json.load(f)

    if a.download or a.all:
        print(f'\n{SEP}')
        print('  STAGE 2-4: Download Episodes → R2')
        print(SEP)
        if not a.dry_run: stage_download(client, r2c, series_map, limit=a.limit)
        else: print('DRY-RUN: skipping download')

    if a.import_db or a.all:
        print(f'\n{SEP}')
        print('  STAGE 5: Import to Database (isActive=False)')
        print(SEP)
        stage_import_db(r2c, dry_run=a.dry_run)

if __name__ == '__main__':
    main()
