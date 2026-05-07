import requests, boto3, urllib3
from botocore.config import Config

urllib3.disable_warnings()

# ── CONFIG ──────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

# From previous run
EP_ID = 'pan33p80t6mc4e4ltqkw1h3v'
SLUG = 'romantis-di-musim-dingin'
SUB_URL = 'https://awscdn.netshort.com/112a293ead1f4f7d9e3116efeeb05e9e?auth_key=1778963458-33863321f6a545e1976d20e1a5d64995-0-42c562216660ee8dd4dc193d56123444&mime_type=text_plain&Expires=1778555262&Signature=2kb82rH45z3jyyEgqMogAprp1D9pYIRvqpYSGY5IjF0OZEtLlRmibzOxjIEua6OdeCz4Uvicjd9bddpCRD~o-AmmpQnmorNtWPMShvPbWDFMP32MtRWQ4ywo6orG8owH~Q1W8pfFQvScEsaz~qA5VhirP5tmo18lpu-klASG0CmCQi3pNMLvIPnFwCqZAjaswiaCQjnoovJRgGRIhhHCD-PYaejMeW0Edv~skWx-Q1eHLCGmcALGOIzvTK5ztEUxy2Lc96iQM3BegOfhQtkru91uxOp~H0afJfieDfSu9xydWj16xch0oBxbe3hNbc-c03TtAL-65qlWijon0-3Kiw__&Key-Pair-Id=K15WUQYEZKHKVU'

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def main():
    print("Downloading subtitle...")
    r = requests.get(SUB_URL, timeout=15, verify=False)
    if not r.ok:
        print(f"Failed to download subtitle: {r.status_code}")
        return
    
    sub_content = r.content
    r2 = get_r2()
    sub_key = f"netshortv2/{SLUG}/ep032.vtt"
    
    print(f"Uploading subtitle to R2: {sub_key}")
    r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_content, ContentType='text/vtt')
    
    final_sub_url = f"{R2_PUBLIC}/{sub_key}"
    print(f"Subtitle URL: {final_sub_url}")
    
    print("Registering subtitle in database...")
    payload = {
        'language': 'id',
        'label': 'Bahasa Indonesia',
        'url': final_sub_url,
        'isDefault': True
    }
    # Check the endpoint for adding subtitles. Based on schema it's likely /api/episodes/{id}/subtitles
    # Looking at admin code: fetch(`/api/episodes/${ep.id}/subtitles`);
    # Standalone script uses: r_sub = requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
    
    url = f"{API_BASE}/api/admin/episodes/{EP_ID}/subtitles" # Trying admin endpoint first
    resp = requests.post(url, headers=ADMIN_HDR, json=payload, timeout=15)
    
    if not resp.ok:
        # Try without /admin
        url = f"{API_BASE}/api/episodes/{EP_ID}/subtitles"
        resp = requests.post(url, headers=ADMIN_HDR, json=payload, timeout=15)

    if resp.ok:
        print("SUCCESS! Subtitle registered.")
    else:
        print(f"FAILED to register subtitle: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
