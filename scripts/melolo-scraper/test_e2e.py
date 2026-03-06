#!/usr/bin/env python3
"""Quick E2E test: download 1 episode, transcode with ffmpeg, check result."""
import requests, json, subprocess, os, tempfile
from pathlib import Path

API = "https://vidrama.asia/api/melolo"
TEMP = Path(tempfile.gettempdir()) / "vidrama_test"
TEMP.mkdir(exist_ok=True)

print("=== E2E TEST: Vidrama → FFmpeg → Verify ===\n")

# 1) Get first drama
print("[1] Search API...")
r = requests.get(f"{API}?action=search&keyword=a&limit=1&offset=0", timeout=10)
drama = r.json()["data"][0]
did = drama["id"]
print(f"    Drama: {drama['title']} (id: {did})")

# 2) Get detail for ep1
print("[2] Detail API...")
r2 = requests.get(f"{API}?action=detail&id={did}", timeout=10)
detail = r2.json()["data"]
total = detail.get("totalEpisodes", len(detail.get("episodes", [])))
print(f"    Episodes: {total}")

# 3) Get stream URL for ep1
print("[3] Stream API (ep1)...")
r3 = requests.get(f"{API}?action=stream&id={did}&episode=1", timeout=10)
stream = r3.json()["data"]
proxy = stream["proxyUrl"]
print(f"    Proxy: {proxy[:60]}...")
print(f"    Quality: {stream.get('quality', '?')}")
print(f"    Duration: {stream.get('duration', '?')}s")

# 4) Download raw MP4
raw_path = TEMP / "raw_test.mp4"
print(f"[4] Downloading raw MP4...")
full_url = f"https://vidrama.asia{proxy}"
resp = requests.get(full_url, timeout=120, stream=True)
resp.raise_for_status()
total_bytes = 0
with open(raw_path, 'wb') as f:
    for chunk in resp.iter_content(chunk_size=1024*1024):
        f.write(chunk)
        total_bytes += len(chunk)
raw_mb = raw_path.stat().st_size / 1024 / 1024
print(f"    Downloaded: {raw_mb:.2f}MB")
print(f"    Content-Type: {resp.headers.get('content-type', '?')}")

# 5) Probe raw file
print("[5] FFprobe raw file...")
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration,size,format_name:stream=codec_name,width,height,bit_rate",
     "-of", "json", str(raw_path)],
    capture_output=True, text=True
)
if probe.returncode == 0:
    info = json.loads(probe.stdout)
    print(f"    {json.dumps(info, indent=4)}")

# 6) Transcode
out_path = TEMP / "transcoded_test.mp4"
print("[6] FFmpeg transcoding...")
cmd = [
    "ffmpeg", "-y", "-i", str(raw_path),
    "-c:v", "libx264", "-preset", "fast", "-crf", "28",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k", "-ac", "2",
    "-movflags", "+faststart",
    str(out_path)
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
if result.returncode == 0:
    out_mb = out_path.stat().st_size / 1024 / 1024
    ratio = (1 - out_mb / raw_mb) * 100
    print(f"    ✅ Transcoded: {out_mb:.2f}MB (was {raw_mb:.2f}MB, {ratio:+.0f}%)")
    
    # Probe output
    probe2 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height",
         "-of", "json", str(out_path)],
        capture_output=True, text=True
    )
    if probe2.returncode == 0:
        info2 = json.loads(probe2.stdout)
        print(f"    {json.dumps(info2, indent=4)}")
else:
    print(f"    ❌ FFmpeg failed!")
    print(f"    stderr: {result.stderr[-300:]}")

# Cleanup
raw_path.unlink(missing_ok=True)
out_path.unlink(missing_ok=True)

print("\n=== TEST COMPLETE ===")
