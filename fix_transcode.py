with open('d:/kingshortid/ingest_shortmax_queue_vps.py', 'r', encoding='utf-8') as f:
    text = f.read()

download_transcode = """
def download_and_transcode(m3u8_url, slug, ep_no):
    import os, subprocess, time
    TEMP_DIR = 'temp_vid'
    os.makedirs(TEMP_DIR, exist_ok=True)
    local_720 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    headers_str = (
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\\r\\n"
        "Referer: https://vidrama.asia/\\r\\n"
    )
    
    # 720p stream copy
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-headers', headers_str,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            break
        else:
            print(f"      ⚠ 720p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
            
    if not success_720:
        return None, None
        
    # 540p transcode
    success_540 = False
    for attempt in range(1, 3):
        cmd_540 = [
            'ffmpeg', '-y', '-i', local_720,
            '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart', '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd_540, capture_output=True, text=True, errors='ignore', timeout=900)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            print(f"      ⚠ 540p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 2: time.sleep(5)
            
    return local_720 if success_720 else None, local_540 if success_540 else None
"""

text = text.replace('def get_or_register_drama', download_transcode + '\n\ndef get_or_register_drama')

with open('d:/kingshortid/ingest_shortmax_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(text)
