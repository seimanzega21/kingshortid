import requests
import boto3
import re
import urllib3
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Config ---
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def has_non_latin(text):
    if not text: return False
    # Detects Chinese, Korean, Japanese characters
    return bool(re.search(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', text))

def delete_from_r2(r2, url):
    if not url or R2_PUBLIC not in url: return
    key = url.replace(f"{R2_PUBLIC}/", "")
    try:
        r2.delete_object(Bucket=R2_BUCKET, Key=key)
        print(f"      - Deleted R2 key: {key}")
    except Exception as e:
        print(f"      - [ERR] R2 delete failed: {e}")

def main():
    print("[START] Cleanup Non-Latin Dramas (Korean/Chinese/Japanese)")
    r2 = get_r2()
    
    # 1. Fetch all dramas
    print("[1] Fetching all dramas from API...")
    resp = requests.get(f"{API_BASE}/api/dramas?limit=2000&includeInactive=true", headers=ADMIN_HDR)
    if not resp.ok:
        print(f"[FATAL] API failed: {resp.text}")
        return
    
    all_dramas = resp.json().get('dramas', [])
    bad_dramas = [d for d in all_dramas if has_non_latin(d['title'])]
    
    print(f"    Found {len(bad_dramas)} dramas with non-latin titles out of {len(all_dramas)}.")
    
    for d in bad_dramas:
        d_id = d['id']
        print(f"\n[CLEANUP] Drama ID: {d_id}")
        
        # 2. Get detail to find all episodes
        try:
            detail_resp = requests.get(f"{API_BASE}/api/dramas/{d_id}?includeInactive=true", headers=ADMIN_HDR)
            if not detail_resp.ok:
                print(f"    [ERROR] Failed to get detail for {d_id}")
                continue
            
            detail = detail_resp.json()
            eps = detail.get('episodes', [])
            
            # Delete Cover
            delete_from_r2(r2, detail.get('cover'))
            
            # Delete Episodes in R2
            for ep in eps:
                delete_from_r2(r2, ep.get('videoUrl'))
                delete_from_r2(r2, ep.get('videoUrl540p'))
            
            # 3. Delete from DB
            del_resp = requests.delete(f"{API_BASE}/api/dramas/{d_id}", headers=ADMIN_HDR)
            if del_resp.ok:
                print(f"    [SUCCESS] Deleted drama from Database.")
            else:
                print(f"    [ERROR] Failed to delete from DB: {del_resp.status_code}")
                
        except Exception as e:
            print(f"    [ERROR] Error processing {d_id}: {type(e).__name__}")

    print("\n[DONE] Cleanup finished.")

if __name__ == "__main__":
    main()
