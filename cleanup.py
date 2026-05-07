import requests, boto3, urllib3
from botocore.config import Config

urllib3.disable_warnings()

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# ── DELETE DRAMAS ──────────────────────────────────────────────────────────────────
ids_to_delete = ['a5t2801mi1n7ubbd5279wnab', 'woxgf5gu2f97cs02mkmjhkln', 'd40yxdr4m35sdkdrw6ezu64n']

for did in ids_to_delete:
    r = requests.delete(f"{API_BASE}/api/admin/dramas/{did}", headers=ADMIN_HDR)
    if r.ok:
        print(f"DELETED drama {did} from DB.")
    else:
        print(f"FAILED to delete {did}: {r.status_code} {r.text}")

# ── DELETE R2 FILES ──────────────────────────────────────────────────────────────────
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                    config=Config(signature_version='s3v4'), region_name='auto')

slugs = ['raja-yang-ditakuti-musuh', 'menghabisi-yang-jahat', 'dua-kuasa-menjadi-satu']
for slug in slugs:
    prefix = f"netshortv2/{slug}/"
    res = r2.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix)
    deleted_count = 0
    for item in res.get('Contents', []):
        try:
            r2.delete_object(Bucket=R2_BUCKET, Key=item['Key'])
            deleted_count += 1
        except: pass
    print(f"DELETED {deleted_count} R2 files for {slug}.")
