import requests
import boto3
import json
import urllib3
from botocore.config import Config

urllib3.disable_warnings()

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

# NO-DUB dramas to delete
NO_DUB_DRAMAS = [
    {'id': '20921', 'slug': 'kakakku-bos-mafia',                    'title': 'Kakakku Bos Mafia'},
    {'id': '21045', 'slug': 'runtuhnya-mahkota',                     'title': 'Runtuhnya Mahkota'},
    {'id': '18698', 'slug': 'berkat-sistem-putri-jadi-milikku',      'title': 'Berkat Sistem'},
    {'id': '18630', 'slug': 'sang-penagih-utang-takdir',             'title': 'Sang Penagih Utang Takdir'},
    {'id': '21614', 'slug': 'putri-disakiti-ayah-ternyata-jenderal', 'title': 'Putri Disakiti'},
    {'id': '20742', 'slug': 'pelindungku-cinta-terlarangku',         'title': 'Pelindungku Cinta Terlarangku'},
    {'id': '20100', 'slug': 'cinta-takkan-berbalik',                 'title': 'Cinta Takkan Berbalik'},
    {'id': '20526', 'slug': 'ratu-hati-sang-pembalap',              'title': 'Ratu Hati Sang Pembalap'},
]

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4')
)

for d in NO_DUB_DRAMAS:
    slug = d['slug']
    title = d['title']
    print(f"\n--- Cleaning: {title} ---")

    # 1. Find and delete from DB
    r = requests.get(f"{API_BASE}/api/dramas", params={"search": title}, timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for dr in dramas:
            if title.lower() in dr.get('title', '').lower():
                drama_id = dr['id']
                del_r = requests.delete(
                    f"{API_BASE}/api/admin/dramas/{drama_id}",
                    headers=ADMIN_HDR, timeout=15
                )
                print(f"  DB delete [{del_r.status_code}]: ID={drama_id}")

    # 2. Delete R2 files
    prefix = f"dramas/netshort/{slug}/"
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix)
    deleted = 0
    for page in pages:
        objects = page.get('Contents', [])
        if objects:
            s3.delete_objects(
                Bucket=R2_BUCKET,
                Delete={'Objects': [{'Key': o['Key']} for o in objects]}
            )
            deleted += len(objects)
    print(f"  R2 deleted: {deleted} files from {prefix}")

print("\nDone! All NO-DUB dramas cleaned up.")
