import requests
import urllib.parse
import os
import subprocess

upstream_id = 'rz3UJ5zFl4'
ep_no = 1
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://vidrama.asia/',
}

r_stream = requests.get(f'https://vidrama.asia/api/dramawavev2?action=stream&id={upstream_id}&episode={ep_no}', headers=HEADERS, timeout=20, verify=False)
data = r_stream.json().get('data', {})
v_url = data.get('videoUrl', '')
if '?url=' in v_url:
    v_url = urllib.parse.unquote(v_url.split('?url=')[1])

sub_url = ''
for sub in data.get('subtitles', []):
    if sub.get('language') == 'id-ID' or sub.get('label') == 'Indonesia':
        sub_url = sub.get('url', '')
        if '?url=' in sub_url:
            sub_url = urllib.parse.unquote(sub_url.split('?url=')[1])
        break

print("Stream URL:", v_url)
print("Subtitle URL:", sub_url)

if sub_url:
    print("Downloading subtitle...")
    r = requests.get(sub_url, headers=HEADERS)
    with open('test_sub.vtt', 'wb') as f:
        f.write(r.content)
    print("Saved test_sub.vtt")

    # Try burning with ffmpeg on a small clip (5 seconds)
    print("Downloading and transcoding 5 seconds with subtitle...")
    cmd = [
        "ffmpeg", "-y", 
        "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://vidrama.asia/\r\n",
        "-i", v_url, 
        "-t", "5", 
        "-vf", "scale=720:-2,subtitles='test_sub.vtt'", 
        "-c:v", "libx264", "-c:a", "aac", 
        "test_hardsub.mp4"
    ]
    subprocess.run(cmd, check=True)
    print("Success")
