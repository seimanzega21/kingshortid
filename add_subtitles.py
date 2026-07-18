import re

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update transcode_to_resolutions signature and logic
old_transcode = '''def transcode_to_resolutions(local_source, ep_no, temp_dir, slug):
    local_720 = os.path.join(temp_dir, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(temp_dir, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    # Transcode 720p (H.264, scale width to 720 vertical, faststart)
    success_720 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', 'scale=720:-2',
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            break
        else:
            log(slug, f"⚠ 720p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
    if not success_720:
        return None, None
        
    # Transcode 540p (H.264, scale width to 540 vertical, faststart)
    success_540 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=540:-2',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            log(slug, f"⚠ 540p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
    if not success_540:
        return local_720, None
        
    return local_720, local_540'''

new_transcode = '''def transcode_to_resolutions(local_source, ep_no, temp_dir, slug, local_sub=None):
    local_720 = os.path.join(temp_dir, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(temp_dir, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    vf_720 = 'scale=720:-2'
    if local_sub and os.path.exists(local_sub):
        vf_720 += f",subtitles='{local_sub}'"
        
    # Transcode 720p
    success_720 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', vf_720,
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            break
        else:
            log(slug, f"⚠ 720p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
    if not success_720:
        return None, None
        
    # Transcode 540p
    vf_540 = 'scale=540:-2'
    success_540 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', vf_540,
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            log(slug, f"⚠ 540p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
    if not success_540:
        return local_720, None
        
    return local_720, local_540'''

content = content.replace(old_transcode, new_transcode)

# 2. Add subtitle downloading in process_drama
old_process_loop = '''        stream_url = None
        try:
            r_stream = requests.get(f'https://vidrama.asia/api/dramawavev2?action=stream&id={upstream_id}&episode={ep_no}', headers=HEADERS, timeout=20, verify=False)
            if r_stream.ok:
                v_url = r_stream.json().get('data', {}).get('videoUrl', '')
                if '?url=' in v_url:
                    import urllib.parse
                    v_url = urllib.parse.unquote(v_url.split('?url=')[1])
                stream_url = v_url
        except Exception as e:
            log(slug, f"⚠ Error fetching stream: {e}")

        if not stream_url:
            log(slug, f"❌ No stream URL found for Ep {ep_no}. Skipping.")
            continue
            
        local_raw = os.path.join(temp_dir, f"ep{ep_no:03d}_raw.mp4")
        
        # Download
        log(slug, f"📥 Downloading Ep {ep_no} source...")
        if not download_source_file(stream_url, local_raw, slug):
            log(slug, f"❌ Failed to download source for Ep {ep_no}. Skipping.")
            continue
            
        # Get duration'''

new_process_loop = '''        stream_url = None
        sub_url = None
        try:
            r_stream = requests.get(f'https://vidrama.asia/api/dramawavev2?action=stream&id={upstream_id}&episode={ep_no}', headers=HEADERS, timeout=20, verify=False)
            if r_stream.ok:
                data = r_stream.json().get('data', {})
                v_url = data.get('videoUrl', '')
                import urllib.parse
                if '?url=' in v_url:
                    v_url = urllib.parse.unquote(v_url.split('?url=')[1])
                stream_url = v_url
                
                # Subtitles
                for sub in data.get('subtitles', []):
                    if sub.get('language') == 'id-ID' or sub.get('label') == 'Indonesia':
                        s_url = sub.get('url', '')
                        if '?url=' in s_url:
                            s_url = urllib.parse.unquote(s_url.split('?url=')[1])
                        sub_url = s_url
                        break
        except Exception as e:
            log(slug, f"⚠ Error fetching stream: {e}")

        if not stream_url:
            log(slug, f"❌ No stream URL found for Ep {ep_no}. Skipping.")
            continue
            
        local_raw = os.path.join(temp_dir, f"ep{ep_no:03d}_raw.mp4")
        local_sub = os.path.join(temp_dir, f"ep{ep_no:03d}.vtt")
        
        # Download Subtitle
        if sub_url:
            try:
                r_sub = requests.get(sub_url, headers=HEADERS, timeout=20)
                if r_sub.ok:
                    with open(local_sub, 'wb') as f:
                        f.write(r_sub.content)
                    log(slug, f"📥 Downloaded subtitle for Ep {ep_no}.")
                else:
                    local_sub = None
            except Exception as e:
                log(slug, f"⚠ Failed to download subtitle: {e}")
                local_sub = None
        else:
            local_sub = None
            
        # Download
        log(slug, f"📥 Downloading Ep {ep_no} source...")
        if not download_source_file(stream_url, local_raw, slug):
            log(slug, f"❌ Failed to download source for Ep {ep_no}. Skipping.")
            continue
            
        # Get duration'''

content = content.replace(old_process_loop, new_process_loop)

# 3. Update transcode call
old_transcode_call = '''        # Transcode
        log(slug, f"⚡ Transcoding Ep {ep_no} to 720p & 540p...")
        local_720, local_540 = transcode_to_resolutions(local_raw, ep_no, temp_dir, slug)'''

new_transcode_call = '''        # Transcode
        log(slug, f"⚡ Transcoding Ep {ep_no} to 720p & 540p...")
        local_720, local_540 = transcode_to_resolutions(local_raw, ep_no, temp_dir, slug, local_sub=local_sub)'''

content = content.replace(old_transcode_call, new_transcode_call)

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Subtitle logic added successfully!")
