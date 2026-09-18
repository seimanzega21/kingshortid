import requests
import urllib3
import re
import json
import boto3
from botocore.config import Config

urllib3.disable_warnings()

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

paginator = s3.get_paginator('list_objects_v2')
all_r2_slugs = set()

for prefix in ['melolov3/', 'melolo/', 'dramas/melolo/', 'dramas/']:
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix, Delimiter='/'):
        for p in page.get('CommonPrefixes', []):
            slug = p['Prefix'].rstrip('/').split('/')[-1]
            all_r2_slugs.add(slug.lower().strip())

def slugify(text):
    text = text.lower().strip()
    slug = re.sub(r'[\W_]+', '-', text).strip('-')
    return slug

# Also check database titles
API_BASE = 'https://api.shortlovers.id/api'
db_titles = set()
page = 1
while True:
    r = requests.get(f'{API_BASE}/dramas?page={page}&limit=100&includeInactive=true', timeout=15)
    if not r.ok: break
    data = r.json()
    dramas = data.get('dramas', [])
    if not dramas: break
    for d in dramas:
        db_titles.add(d['title'].lower().strip())
    if len(dramas) < 100: break
    page += 1

print(f"Loaded {len(all_r2_slugs)} R2 slugs and {len(db_titles)} DB titles.")

# Search keywords to discover popular/new melolov3 dramas
keywords = [
    "cinta", "raja", "dewa", "nikah", "kaya", "kembali", "istri", "suami",
    "bos", "mafia", "naga", "anak", "ayah", "ibu", "desa", "putri", "sakti",
    "miliarder", "rahasia", "takdir", "bangkit", "dendam", "presiden", "harta"
]

discovered_dramas = {}
headers = {'User-Agent': 'Mozilla/5.0'}

for kw in keywords:
    try:
        url = f"https://vidrama.asia/api/melolov3/search?q={kw}&lang=id"
        r = requests.get(url, headers=headers, verify=False, timeout=12)
        if not r.ok:
            continue
        items = r.json().get('items', [])
        for item in items:
            book_id = str(item.get('book_id'))
            title = item.get('title', '').strip()
            if not book_id or not title:
                continue
            if book_id not in discovered_dramas:
                discovered_dramas[book_id] = item
    except Exception as e:
        print(f"Error searching {kw}: {e}")

print(f"Total unique melolov3 dramas discovered: {len(discovered_dramas)}")

# Filter out what's already in R2 or Database
available_new = []
for book_id, item in discovered_dramas.items():
    title = item.get('title', '').strip()
    slug = slugify(title)

    # Check if in R2 or in DB
    in_r2 = slug in all_r2_slugs
    in_db = title.lower() in db_titles

    if not in_r2 and not in_db:
        available_new.append({
            'book_id': book_id,
            'title': title,
            'slug': slug,
            'status': item.get('status'),
            'cover': item.get('cover'),
            'abstract': item.get('abstract', '')[:120]
        })

print(f"New candidate dramas (NOT in R2 and NOT in DB): {len(available_new)}")

with open('discovered_melolov3_new.json', 'w', encoding='utf-8') as f:
    json.dump(available_new, f, indent=2, ensure_ascii=False)
