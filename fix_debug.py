import re

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_download_func = '''def download_source_file(url, local_path, slug):
    try:
        import subprocess
        # Pass headers to ffmpeg so it doesn't get 403 Forbidden from CDN
        headers = r"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://vidrama.asia/\r\n"
        log(slug, f"URL is {url}")
        cmd = ["ffmpeg", "-y", "-headers", headers, "-i", url, "-c", "copy", local_path]
        # We let stderr flow to the log so we can debug why it fails
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL)
        if res.returncode == 0:
            import os
            size = os.path.getsize(local_path)
            log(slug, f"Downloaded {size} bytes")
            if size < 1000:
                return False
            return True
        else:
            return False
    except Exception as e:
        log(slug, f"⚠ Error downloading: {e}")
        return False'''

content = re.sub(
    r'def download_source_file\(url, local_path, slug\):.*?return False',
    new_download_func,
    content,
    flags=re.DOTALL
)

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(content)
