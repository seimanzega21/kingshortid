import requests, json, os, boto3
from dotenv import load_dotenv

load_dotenv('d:/kingshortid/scripts/melolo-scraper/.env')

BACKEND_URL = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
HEADERS = {"Authorization": f"Bearer {ADMIN_KEY}", "X-Admin-Key": ADMIN_KEY}

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")

s3 = boto3.client("s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto"
)

# Fetch all dramas
r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", headers=HEADERS)
dramas = r.json()
if isinstance(dramas, dict):
    dramas = dramas.get("dramas", [])

for drama in dramas:
    drid = drama["id"]
    er = requests.get(f"{BACKEND_URL}/dramas/{drid}/episodes", headers=HEADERS)
    eps = er.json()
    if isinstance(eps, dict):
        eps = eps.get("episodes", [])
        
    for ep in eps:
        epid = ep["id"]
        # Fetch subtitles
        sr = requests.get(f"{BACKEND_URL}/episodes/{epid}/subtitles", headers=HEADERS)
        if sr.status_code != 200:
            continue
        subs = sr.json()
        if isinstance(subs, dict):
            subs = subs.get("subtitles", [])
            
        for sub in subs:
            old_url = sub["url"]
            if old_url.endswith(".srt"):
                new_url = old_url[:-4] + ".vtt"
                print(f"Fixing db subtitle {sub['id']} to {new_url}...")
                
                # Delete Old Sub
                requests.delete(
                    f"{BACKEND_URL}/episodes/{epid}/subtitles/{sub['id']}",
                    headers=HEADERS
                )
                
                # Create New Sub
                requests.post(
                    f"{BACKEND_URL}/episodes/{epid}/subtitles",
                    json={
                        "language": sub["language"],
                        "label": sub["label"],
                        "url": new_url,
                        "isDefault": sub.get("isDefault", False)
                    },
                    headers=HEADERS
                )
                
                # Copy R2 object (stripping https://stream.shortlovers.id/)
                old_key = old_url.replace("https://stream.shortlovers.id/", "")
                new_key = new_url.replace("https://stream.shortlovers.id/", "")
                
                try:
                    s3.copy_object(
                        Bucket=R2_BUCKET,
                        CopySource=f"{R2_BUCKET}/{old_key}",
                        Key=new_key,
                        ContentType="text/vtt"
                    )
                    # Delete old
                    s3.delete_object(Bucket=R2_BUCKET, Key=old_key)
                    print(f"  Moved R2: {old_key} -> {new_key}")
                except Exception as e:
                    print(f"  Failed to move R2: {e}")

print("Fixed subtitles!")
