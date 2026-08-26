import re

with open('ingest_netshort_local.py', 'r', encoding='utf-8') as f:
    s = f.read()

new_cover_func = """
def upload_cover(r2, cover_url, slug):
    import urllib.parse
    key = f"dramas/covers/{slug}_cover_hq.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return f"{R2_PUBLIC}/{key}"
    except Exception:
        pass
    
    try:
        r = requests.get(cover_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30, verify=False)
        if r.ok:
            raw_path = f"{TEMP_DIR}/raw_cover_{slug}.tmp"
            jpg_path = f"{TEMP_DIR}/cover_{slug}.jpg"
            with open(raw_path, 'wb') as out:
                out.write(r.content)
            
            subprocess.run(['ffmpeg', '-y', '-i', raw_path, '-update', '1', jpg_path], capture_output=True)
            
            if os.path.exists(jpg_path):
                with open(jpg_path, 'rb') as out:
                    r2.upload_fileobj(
                        out, R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
                    )
                return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"      Cover upload failed: {e}")
    return cover_url
"""

s = re.sub(r'def upload_cover\(r2, cover_url, slug\):.*?return cover_url', new_cover_func.strip(), s, flags=re.DOTALL)

with open('ingest_netshort_local.py', 'w', encoding='utf-8') as f:
    f.write(s)
