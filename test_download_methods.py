# -*- coding: utf-8 -*-
"""
Test berbagai cara download video dari stardusttv CDN
"""
import subprocess
import sys
import os
import requests
import urllib3

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

M3U8_URL = 'https://mmcdn-v.stardust-tv.com/%E5%8D%B0%E5%B0%BC%E8%AF%AD/%E6%88%91%E6%9C%89%E4%B8%80%E5%89%91%EF%BC%8C%E5%8F%AF%E6%96%A9%E9%98%8E%E7%BD%97_ID_DUB/h264/Satu%20Pedang,%20Tebas%20Raja%20Neraka_001/59296e557a9949f4a8238ab67e431dad.m3u8'
OUT = 'D:/kingshortid/temp_raja/test_ep1.mp4'
os.makedirs('D:/kingshortid/temp_raja', exist_ok=True)

# Test 1: Try accessing m3u8 directly with requests
print("=== TEST 1: Direct HTTP Access to m3u8 ===")
for referer in ['https://vidrama.asia/', 'https://stardust-tv.com/', '']:
    try:
        hdrs = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': referer,
        }
        r = requests.get(M3U8_URL, headers=hdrs, timeout=10, verify=False)
        print(f"  Referer={referer[:40] or 'none'} -> {r.status_code}, len={len(r.text)}")
        if r.ok and '#' in r.text:
            print(f"  CONTENT: {r.text[:200]}")
            break
    except Exception as e:
        print(f"  Referer={referer[:40] or 'none'} -> ERROR: {e}")

# Test 2: ffmpeg with -allowed_extensions ALL
print("\n=== TEST 2: FFmpeg with allowed_extensions ===")
cmd = [
    'ffmpeg', '-y',
    '-allowed_extensions', 'ALL',
    '-protocol_whitelist', 'file,crypto,data,http,https,tcp,tls',
    '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\nReferer: https://vidrama.asia/\r\n',
    '-i', M3U8_URL,
    '-t', '15',
    '-c', 'copy',
    '-loglevel', 'error',
    OUT
]
res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=60)
if res.returncode == 0 and os.path.exists(OUT) and os.path.getsize(OUT) > 10000:
    print(f"  ✅ FFmpeg SUCCESS! Size: {os.path.getsize(OUT)/1024/1024:.2f} MB")
else:
    print(f"  ❌ FFmpeg failed: {res.stderr[-300:]}")
    if os.path.exists(OUT): os.remove(OUT)

# Test 3: yt-dlp on m3u8 directly with cookies from browser
print("\n=== TEST 3: yt-dlp on m3u8 with --cookies-from-browser ===")
cmd3 = [
    'yt-dlp',
    '--no-update',
    '-o', OUT,
    '--add-header', 'Referer:https://vidrama.asia/',
    '--add-header', 'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    '-f', 'best',
    '--download-sections', '*0-15',
    M3U8_URL
]
res3 = subprocess.run(cmd3, capture_output=True, text=True, errors='ignore', timeout=60)
if res3.returncode == 0 and os.path.exists(OUT) and os.path.getsize(OUT) > 10000:
    print(f"  ✅ yt-dlp SUCCESS! Size: {os.path.getsize(OUT)/1024/1024:.2f} MB")
else:
    print(f"  ❌ yt-dlp failed: stdout={res3.stdout[-200:]} stderr={res3.stderr[-200:]}")

# Test 4: Check if the domain is actually accessible
print("\n=== TEST 4: DNS/connectivity test ===")
import socket
try:
    ip = socket.gethostbyname('mmcdn-v.stardust-tv.com')
    print(f"  DNS resolved: mmcdn-v.stardust-tv.com -> {ip}")
except Exception as e:
    print(f"  DNS FAILED: {e}")

# Test 5: Try downloading via requests + chunked save
print("\n=== TEST 5: Get m3u8 content to see segment URLs ===")
try:
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://vidrama.asia/',
        'Origin': 'https://vidrama.asia',
    }
    r = requests.get(M3U8_URL, headers=hdrs, timeout=15, verify=False)
    print(f"  Status: {r.status_code}")
    print(f"  Content: {r.text[:500] if r.ok else r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
