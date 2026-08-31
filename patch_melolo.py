import re

with open('ingest_melolov3_local.py', 'r', encoding='utf-8') as f:
    s = f.read()

# 1. Update isActive and status
s = s.replace("'isActive': True,", "'isActive': False,")
s = s.replace("'isActive': True", "'isActive': False")
if "'status': 'completed'" not in s and "'status': 'pending'" not in s:
    s = s.replace("'isActive': False,", "'isActive': False,\n        'status': 'pending',")
s = s.replace("'status': 'completed'", "'status': 'pending'")
s = s.replace("requests.post(f\"{API_BASE}/admin/dramas\", headers=ADMIN_HDR, json={'id': db_id, 'isActive': True}, timeout=10)", "")

# 2. Update ffmpeg commands with cfr and aresample
s = s.replace(
    "'-c:v', 'libx264', '-crf', '23', '-preset', 'fast',", 
    "'-c:v', 'libx264', '-crf', '23', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1',"
)
s = s.replace(
    "'-c:v', 'libx264', '-crf', '26', '-preset', 'fast',", 
    "'-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1',"
)

# 3. Update cover upload to use ffmpeg
new_cover = """def upload_cover_to_r2(r2, cover_url, slug, temp_dir):
    import subprocess
    if not cover_url: return ""
    local_raw = os.path.join(temp_dir, f"{slug}_cover.tmp")
    local_jpg = os.path.join(temp_dir, f"{slug}_cover_hq.jpg")
    r2_key = f"dramas/covers/{slug}_cover_hq.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        return f"{R2_PUBLIC}/{r2_key}"
    except: pass
    
    try:
        r = requests.get(cover_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30, verify=False)
        if r.ok:
            with open(local_raw, 'wb') as f:
                f.write(r.content)
            subprocess.run(['ffmpeg', '-y', '-i', local_raw, '-update', '1', local_jpg], capture_output=True)
            if os.path.exists(local_jpg):
                r2.upload_file(local_jpg, R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
                return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        log(slug, f" Cover upload failed: {e}")
    return ""
"""
s = re.sub(r'def upload_cover_to_r2.*?return ""\n', new_cover, s, flags=re.DOTALL)

with open('ingest_melolov3_local.py', 'w', encoding='utf-8') as f:
    f.write(s)
