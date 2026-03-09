"""
Stage 4: Import Dubbed Dramas from R2 to Database
==================================================
Reads metadata.json per drama from R2 and inserts to PostgreSQL:
- Drama: status=ongoing/completed, isActive=FALSE (pending review)
- Episode: videoUrl from R2 MP4, isActive=FALSE
- Subtitle: Indonesian subtitle URL

Dramas imported as PENDING (isActive=False) — admin must activate before mobile sees them.

Run: python import_to_db.py [--test] [--drama-folder FOLDER]
"""
import json, sys, time, re
import psycopg2
from pathlib import Path
import boto3
from botocore.config import Config
import base64

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PREFIX    = 'freereels/'  # Scan only freereels dramas

SOURCE_IDS_FILE = Path('dubbed_series_ids.json')   # From discover_dramas.py

GENRES_MAP = {
    'Drama': 'Drama',
    'Romance': 'Romance',
    'Romantis': 'Romance',
    'Bisnis': 'Business',
    'Aksi': 'Action',
    'Komedi': 'Comedy',
    'Thriller': 'Thriller',
    'Misteri': 'Mystery',
    'Fantasi': 'Fantasy',
    'Sejarah': 'Historical',
    'Kampus': 'School',
    'Keluarga': 'Family',
    'Balas Dendam': 'Revenge',
    'Kontemporer': 'Contemporary',
}

def map_genres(raw_genres):
    """Translate Indonesian genre names to English."""
    result = []
    for g in raw_genres:
        mapped = GENRES_MAP.get(g, g)
        if mapped and mapped not in result:
            result.append(mapped)
    if not result:
        result = ['Drama', 'Romance']
    return result

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto',
    )

def list_r2_meta_files(r2):
    """List all metadata.json files in freereels/ prefix."""
    files = []
    token = None
    while True:
        kwargs = {'Bucket': R2_BUCKET, 'Prefix': R2_PREFIX, 'MaxKeys': 1000}
        if token: kwargs['ContinuationToken'] = token
        resp = r2.list_objects_v2(**kwargs)
        for obj in resp.get('Contents', []):
            if obj['Key'].endswith('/metadata.json'):
                files.append(obj['Key'])
        token = resp.get('NextContinuationToken')
        if not token: break
    return files

def read_r2_json(r2, key):
    """Read and parse JSON from R2."""
    try:
        obj = r2.get_object(Bucket=R2_BUCKET, Key=key)
        return json.loads(obj['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f'  R2 read error {key}: {e}')
        return None

# ── DB HELPERS ────────────────────────────────────────────────────────────────
def check_existing_drama(cur, series_id, title):
    """Check if drama already imported (by sourceId in description or title)."""
    cur.execute(
        'SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1',
        (f'%[SourceID: {series_id}]%',)
    )
    row = cur.fetchone()
    if row: return row[0]
    return None

def insert_drama(cur, meta):
    """Insert drama with isActive=FALSE (pending)."""
    title       = meta.get('titleClean') or meta.get('title', 'Unknown')
    desc        = meta.get('description', '') or f'Drama pendek Indonesia dengan sulih suara.'
    cover       = meta.get('cover', '')
    genres      = map_genres(meta.get('genres', []))
    tags        = meta.get('tags', []) + meta.get('content_tags', [])
    total_eps   = meta.get('totalEpisodes', 0)
    source_id   = meta.get('series_id', '')
    status      = 'completed' if meta.get('status') == 'complete' else 'ongoing'
    lang        = meta.get('language', 'Indonesia')
    country     = meta.get('country', 'China')
    views       = meta.get('viewCount', 0)

    # Append source ID to description for dedup check
    full_desc = f'{desc}\n\n[SourceID: {source_id}]'

    cur.execute("""
        INSERT INTO "Drama" (
            id, title, description, cover, banner,
            genres, "tagList", "totalEpisodes",
            rating, views, likes,
            "reviewCount", "averageRating",
            status, "isVip", "isFeatured", "isActive",
            "ageRating", country, language,
            "createdAt", "updatedAt"
        ) VALUES (
            gen_random_uuid(), %s, %s, %s, %s,
            %s::text[], %s::text[], %s,
            0, %s, 0,
            0, 0,
            %s, false, false, false,
            'all', %s, %s,
            NOW(), NOW()
        ) RETURNING id
    """, (
        title, full_desc, cover, cover,
        genres, tags, total_eps,
        views, status, country, lang
    ))
    return cur.fetchone()[0]

def insert_episode(cur, drama_id, ep, ep_num):
    """Insert episode with isActive=FALSE."""
    video_url = ep.get('videoUrl', '')
    thumb     = ep.get('cover', '')
    duration  = ep.get('duration', 0)
    title     = ep.get('title', f'Episode {ep_num}')
    
    if not video_url:
        return False  # Skip episodes without video
    
    # Check duplicate
    cur.execute(
        'SELECT id FROM "Episode" WHERE "dramaId"=%s AND "episodeNumber"=%s',
        (drama_id, ep_num)
    )
    if cur.fetchone():
        return False  # Already exists
    
    cur.execute("""
        INSERT INTO "Episode" (
            id, "dramaId", "episodeNumber",
            title, description, thumbnail, "videoUrl", duration,
            "isVip", "coinPrice", views,
            "isActive", "releaseDate",
            "createdAt", "updatedAt"
        ) VALUES (
            gen_random_uuid(), %s, %s,
            %s, %s, %s, %s, %s,
            false, 0, 0,
            false, NOW(),
            NOW(), NOW()
        ) RETURNING id
    """, (
        drama_id, ep_num,
        title, '', thumb, video_url, duration,
    ))
    ep_id = cur.fetchone()[0]
    return ep_id

def insert_subtitle(cur, episode_id, vtt_url, srt_url=''):
    """Insert Indonesian subtitle record."""
    if not vtt_url and not srt_url:
        return
    url = vtt_url or srt_url
    try:
        cur.execute(
            'SELECT id FROM "Subtitle" WHERE "episodeId"=%s AND language=%s',
            (episode_id, 'id')
        )
        if cur.fetchone(): return
        
        cur.execute("""
            INSERT INTO "Subtitle" (
                id, "episodeId", language, label, url, "isDefault",
                "createdAt"
            ) VALUES (
                gen_random_uuid(), %s, %s, %s, %s, true, NOW()
            )
        """, (episode_id, 'id', 'Bahasa Indonesia', url))
    except Exception as e:
        print(f'    Subtitle error: {e}')

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(description='Import Dubbed Dramas from R2 to DB')
    p.add_argument('--test',           action='store_true', help='Dry run — no DB writes')
    p.add_argument('--drama-folder',   help='Import single drama folder only')
    p.add_argument('--limit',          type=int, help='Max dramas to import')
    a = p.parse_args()

    print('═'*55)
    print('  FreeReels Dubbed → Database Import')
    print('═'*55)
    print(f'  DB: {DATABASE_URL.split("@")[-1]}')
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')
    print()

    r2 = get_r2()

    # Find all metadata files in R2
    print('[1/3] Scanning R2 for drama metadata...')
    meta_files = list_r2_meta_files(r2)
    
    if a.drama_folder:
        meta_files = [f for f in meta_files if f'/{a.drama_folder}/' in f]
    if a.limit:
        meta_files = meta_files[:a.limit]
    
    print(f'  Found {len(meta_files)} dramas in R2 freereels/ prefix')
    
    if not meta_files:
        print('[STOP] No metadata files found. Run download_pipeline.py first.')
        sys.exit(0)

    # Connect DB
    conn = None
    if not a.test:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()
        print('[2/3] Connected to database ✓')
    else:
        cur = None
        print('[2/3] [DRY-RUN] Skipping DB connection')

    # Import
    print(f'\n[3/3] Importing {len(meta_files)} dramas...\n')
    imported_dramas   = 0
    skipped_dramas    = 0
    imported_episodes = 0
    imported_subs     = 0
    failed_dramas     = 0

    for i, meta_key in enumerate(meta_files, 1):
        meta = read_r2_json(r2, meta_key)
        if not meta:
            failed_dramas += 1
            continue
        
        sid   = meta.get('series_id', '')
        title = meta.get('titleClean') or meta.get('title', '?')
        eps   = meta.get('episodes', [])
        uploaded_eps = [ep for ep in eps if ep.get('uploaded') or ep.get('videoUrl')]
        
        print(f'[{i:03d}/{len(meta_files)}] {title[:45]}')
        print(f'          episodes_uploaded={len(uploaded_eps)}/{len(eps)}')
        
        if len(uploaded_eps) == 0:
            print(f'  SKIP: no uploaded episodes')
            skipped_dramas += 1
            continue
        
        if a.test:
            print(f'  [DRY-RUN] Would import {len(uploaded_eps)} episodes')
            imported_dramas += 1
            continue
        
        try:
            # Check for existing drama
            existing_id = check_existing_drama(cur, sid, title)
            
            if existing_id:
                drama_id = existing_id
                print(f'  Drama already exists (id={drama_id[:8]}...), updating episodes...')
            else:
                drama_id = insert_drama(cur, meta)
                imported_dramas += 1
                print(f'  ✓ Drama inserted (id={drama_id[:8]}..., isActive=False)')
            
            # Insert episodes
            ep_ok = ep_skip = 0
            for ep in uploaded_eps:
                ep_num   = ep.get('episode', 0)
                sub_vtt  = ep.get('subtitleVtt', '') or ep.get('indonesianSubVtt', '')
                sub_srt  = ep.get('indonesianSubSrt', '')
                
                ep_id = insert_episode(cur, drama_id, ep, ep_num)
                
                if ep_id:
                    ep_ok += 1
                    imported_episodes += 1
                    if sub_vtt or sub_srt:
                        insert_subtitle(cur, ep_id, sub_vtt, sub_srt)
                        imported_subs += 1
                else:
                    ep_skip += 1
            
            conn.commit()
            print(f'  ✓ Episodes: {ep_ok} inserted, {ep_skip} skipped')
        
        except Exception as e:
            if conn:
                conn.rollback()
            print(f'  ✗ ERROR: {e}')
            import traceback; traceback.print_exc()
            failed_dramas += 1

    # Summary
    print(f'\n{"═"*55}')
    print(f'  ✓ Dramas imported: {imported_dramas}')
    print(f'  ⊘ Skipped: {skipped_dramas}')
    print(f'  ✗ Failed: {failed_dramas}')
    print(f'  📺 Episodes imported: {imported_episodes}')
    print(f'  💬 Subtitles imported: {imported_subs}')
    print(f'\n  ⚠️  All dramas imported with isActive=False')
    print(f'  ⚠️  Go to Admin Dashboard → Dramas to activate/publish')
    print(f'{"═"*55}')

    if conn:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
