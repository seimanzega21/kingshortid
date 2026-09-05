import requests, boto3
from botocore.config import Config

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'
DRAMA_ID_DB = 'kjhmxxf2mk12ulrr7eqcyl8m'
DRAMA_SLUG  = 'hati-yang-dihancurkan'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET, config=Config(signature_version='s3v4'), region_name='auto')

print("STEP 1: Renaming files in R2 to append _v2 to bust cache...")
for i in range(1, 53):
    for res in ['720p', '540p']:
        old_key = f"dramas/{DRAMA_SLUG}/ep{i:03d}_{res}.mp4"
        new_key = f"dramas/{DRAMA_SLUG}/ep{i:03d}_v2_{res}.mp4"
        try:
            r2.copy_object(Bucket=R2_BUCKET, CopySource={'Bucket': R2_BUCKET, 'Key': old_key}, Key=new_key)
            print(f"  Copied to {new_key}")
        except Exception as e:
            print(f"  Failed {old_key}: {e}")

print("\nSTEP 2: Updating DB to point to _v2 URLs...")
er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
eps = er.json()

for ep in eps:
    num = int(ep.get('episodeNumber'))
    ep_id = ep['id']
    
    url720 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{num:03d}_v2_720p.mp4"
    url540 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{num:03d}_v2_540p.mp4"
    
    payload = {
        'videoUrl': url720,
        'videoUrl540p': url540,
    }
    
    upd = requests.put(f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep_id}", headers=ADMIN_HDR, json=payload, timeout=20)
    if upd.ok:
        print(f"  ✅ DB Updated: EP{num}")
    else:
        # try without /dramas
        upd = requests.patch(f"{API_BASE}/api/admin/episodes/{ep_id}", headers=ADMIN_HDR, json=payload, timeout=20)
        if upd.ok:
            print(f"  ✅ DB Patched: EP{num}")
        else:
            upd = requests.put(f"{API_BASE}/api/episodes/{ep_id}", headers=ADMIN_HDR, json=payload, timeout=20)
            if upd.ok:
                print(f"  ✅ DB API Updated: EP{num}")
            else:
                # one more try
                upd = requests.patch(f"{API_BASE}/api/episodes/{ep_id}", headers=ADMIN_HDR, json=payload, timeout=20)
                if upd.ok:
                    print(f"  ✅ DB API Patched: EP{num}")
                else:
                    print(f"  ❌ DB Failed EP{num}: {upd.status_code}")

print("\nDONE!")
