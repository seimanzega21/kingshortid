import requests
import urllib.parse
import subprocess

upstream_id = 'rz3UJ5zFl4'
ep_no = 1
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r_stream = requests.get(f'https://vidrama.asia/api/dramawavev2?action=stream&id={upstream_id}&episode={ep_no}', headers=HEADERS, timeout=20, verify=False)
v_url = r_stream.json().get('data', {}).get('videoUrl', '')
print("Original v_url:", v_url)

if '?url=' in v_url:
    v_url = urllib.parse.unquote(v_url.split('?url=')[1])

print("Parsed v_url:", v_url)

# Test ffmpeg locally
cmd = ["ffmpeg", "-y", "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://vidrama.asia/\r\n", "-i", v_url, "-c", "copy", "test_ep1.mp4"]
print("Running ffmpeg...")
try:
    subprocess.run(cmd, check=True)
    print("Success")
except Exception as e:
    print("Error:", e)
