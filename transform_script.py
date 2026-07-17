import shutil
import re

shutil.copy2('d:/kingshortid/ingest_melolov3_queue_vps.py', 'd:/kingshortid/ingest_dramawavev2_queue_vps.py')

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update queue
start = content.find("DRAMAS_QUEUE = [")
end = content.find("def get_r2():")
new_queue = '''DRAMAS_QUEUE = [
    {'id': 'rz3UJ5zFl4', 'slug': 'ratu-tersembunyi-membalas', 'genres': ['Drama', 'Aksi', 'Balas Dendam']},
]

'''
content = content[:start] + new_queue + content[end:]

# 2. Update provider
content = content.replace('PROVIDER = "melolov3"', 'PROVIDER = "dramawavev2"')
content = content.replace('temp_melolo', 'temp_dramawavev2')

# 3. Update fetch_drama_details
old_fetch = '''def fetch_drama_details(upstream_id, slug):
    detail_url = f'https://vidrama.asia/api/melolov3/series?id={upstream_id}&lang=id'
    videos_url = f'https://vidrama.asia/api/melolov3/multi-video?id={upstream_id}&lang=id'
    
    metadata = {}
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=20, verify=False)
        if r.ok:
            metadata = r.json().get('series') or {}
    except Exception as e:
        log(slug, f"⚠ Error fetching metadata: {e}")
        
    episodes = []
    try:
        r = requests.get(videos_url, headers=HEADERS, timeout=20, verify=False)
        if r.ok:
            data = r.json()
            episodes = data.get('episodes') or data or []
    except Exception as e:
        log(slug, f"⚠ Error fetching episodes: {e}")
        
    return metadata, episodes'''

new_fetch = '''def fetch_drama_details(upstream_id, slug):
    detail_url = f'https://vidrama.asia/api/dramawavev2?action=detail&id={upstream_id}'
    metadata = {}
    episodes = []
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=20, verify=False)
        if r.ok:
            data = r.json().get('data', {})
            metadata = data
            chapter_count = data.get('chapterCount', 0)
            episodes = [{"index": i} for i in range(1, chapter_count + 1)]
    except Exception as e:
        log(slug, f"⚠ Error fetching metadata: {e}")
    return metadata, episodes'''
content = content.replace(old_fetch, new_fetch)

# 4. Update process_drama stream fetching
old_fetch_stream = '''        stream_url = ep.get('stream_url')
        if not stream_url:'''
    
new_fetch_stream = '''        stream_url = None
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

        if not stream_url:'''
content = content.replace(old_fetch_stream, new_fetch_stream)

# 5. Update download_source_file to use ffmpeg
old_download = '''def download_source_file(url, local_path, slug):
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, verify=False, stream=True)
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            log(slug, f"⚠ Error downloading: HTTP {r.status_code}")
            return False
    except Exception as e:
        log(slug, f"⚠ Error downloading: {e}")
        return False'''

new_download = '''def download_source_file(url, local_path, slug):
    try:
        import subprocess
        # Pass headers to ffmpeg so it doesn't get 403 Forbidden from CDN
        headers = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\\r\\nReferer: https://vidrama.asia/\\r\\n'
        log(slug, f"URL is {url}")
        cmd = ["ffmpeg", "-y", "-headers", headers, "-i", url, "-c", "copy", local_path]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            import os
            size = os.path.getsize(local_path)
            log(slug, f"Downloaded {size} bytes")
            if size < 1000:
                return False
            return True
        else:
            return False
    except subprocess.CalledProcessError as e:
        log(slug, f"⚠ Error downloading with ffmpeg: {e}")
        return False
    except Exception as e:
        log(slug, f"⚠ Error downloading: {e}")
        return False'''
content = content.replace(old_download, new_download)

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Transformation complete!")
