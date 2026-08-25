import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_transcode = """def download_and_transcode(mp4_url, ep_no):
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    # 1. Download and transcode to 720p directly from m3u8
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-headers', 'Referer: https://vidrama.asia/\\r\\n',
            '-i', mp4_url,
            '-vf', 'scale=-2:720',
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        import subprocess, time, os
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=600)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 100000:
            success_720 = True
            break
        else:
            print(f"      ⚠ 720p Download/Transcode Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
            
    if not success_720:
        return None, None
        
    # 540p transcode
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1200k', '-bufsize', '2400k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            print(f"      ⚠ 540p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
            
    if not success_540:
        return local_720, None
        
    return local_720, local_540"""

text = re.sub(r'def download_and_transcode\(mp4_url, ep_no\):.*?return local_720, local_540', new_transcode, text, flags=re.DOTALL)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
