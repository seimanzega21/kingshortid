import re, os

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_transcode = """def download_and_transcode(mp4_url, ep_no):
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    local_ts  = os.path.join(TEMP_DIR, f"source_ep{ep_no:03d}.ts")
    
    for f in [local_720, local_540, local_ts]:
        if os.path.exists(f): os.remove(f)
        
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        
        # 1. Download m3u8 playlist
        print(f"      ⇩ Fetching playlist using cloudscraper...")
        r_m3u8 = scraper.get(mp4_url, timeout=30)
        r_m3u8.raise_for_status()
        m3u8_text = r_m3u8.text
        
        # 2. Extract .ts segments
        import urllib.parse
        parsed_url = urllib.parse.urlparse(mp4_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{os.path.dirname(parsed_url.path)}/"
        
        segments = []
        for line in m3u8_text.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle relative paths by appending the query string from the original m3u8 url
                ts_url = urllib.parse.urljoin(base_url, line)
                if parsed_url.query:
                    ts_url += f"?{parsed_url.query}"
                segments.append(ts_url)
                
        if not segments:
            print(f"      ⚠ No segments found in m3u8.")
            return None, None
            
        # 3. Download and concatenate segments
        print(f"      ⇩ Downloading {len(segments)} segments...")
        with open(local_ts, 'wb') as f_out:
            for i, ts_url in enumerate(segments):
                for attempt in range(3):
                    try:
                        r_ts = scraper.get(ts_url, timeout=30)
                        r_ts.raise_for_status()
                        f_out.write(r_ts.content)
                        break
                    except Exception as e:
                        if attempt == 2:
                            print(f"      ⚠ Failed to download segment {i+1}: {e}")
                            return None, None
                        time.sleep(2)
                        
        # 4. Transcode with ffmpeg
        import subprocess
        success_720 = False
        cmd_720 = [
            'ffmpeg', '-y',
            '-i', local_ts,
            '-vf', 'scale=-2:720',
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd_720, capture_output=True, text=True, errors='ignore', timeout=600)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 100000:
            success_720 = True
        else:
            print(f"      ⚠ 720p Transcode failed: {res.stderr.strip()[-200:]}")
            
        if not success_720:
            if os.path.exists(local_ts): os.remove(local_ts)
            return None, None
            
        # 540p transcode
        success_540 = False
        cmd_540 = [
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
        res = subprocess.run(cmd_540, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            
        if os.path.exists(local_ts): os.remove(local_ts)
        
        if not success_540:
            return local_720, None
        return local_720, local_540
        
    except Exception as e:
        print(f"      ⚠ Download/Transcode Exception: {e}")
        return None, None"""

text = re.sub(r'def download_and_transcode\(mp4_url, ep_no\):.*?return local_720, local_540', new_transcode, text, flags=re.DOTALL)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
