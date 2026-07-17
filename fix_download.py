import re

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_download_func = '''def download_source_file(url, local_path, slug):
    try:
        import subprocess
        # Dramawave returns m3u8, we must use ffmpeg to download it to a local mp4
        cmd = ["ffmpeg", "-y", "-i", url, "-c", "copy", local_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError as e:
        log(slug, f"⚠ Error downloading with ffmpeg: {e}")
        return False
    except Exception as e:
        log(slug, f"⚠ Error: {e}")
        return False'''

# We need to replace the old download_source_file
content = re.sub(
    r'def download_source_file\(url, local_path, slug\):.*?return True\n.*?return False\n.*?return False',
    new_download_func,
    content,
    flags=re.DOTALL
)

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(content)
