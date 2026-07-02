import requests
import subprocess
import os
from pathlib import Path

url = "https://stream.shortlovers.id/melolo/anak-fana-penakluk-langit/ep004.mp4"
local_720 = Path("d:/kingshortid/scratch/ep004.mp4")
local_540 = Path("d:/kingshortid/scratch/ep004_540.mp4")

if not local_720.exists():
    print("Downloading ep004.mp4...")
    r = requests.get(url)
    with open(local_720, 'wb') as f:
        f.write(r.content)
    print("Downloaded! Size:", local_720.stat().st_size / (1024*1024), "MB")
else:
    print("ep004.mp4 already downloaded.")

# Test 1: Standard command
print("\n--- Test 1: Standard command ---")
cmd1 = [
    'ffmpeg', '-y', '-i', str(local_720),
    '-vf', 'scale=-2:540',
    '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast',
    '-maxrate', '800k', '-bufsize', '1600k',
    '-c:a', 'aac', '-b:a', '96k',
    '-movflags', '+faststart',
    str(local_540)
]
p = subprocess.run(cmd1, capture_output=True, text=True)
print("Exit code:", p.returncode)
if p.returncode != 0:
    print("Error output:\n", p.stderr[-500:])

# Test 2: Try ignoring decoding errors (using -err_detect ignore_err or ignoring decode errors)
print("\n--- Test 2: Copy audio, ignore decode errors ---")
cmd2 = [
    'ffmpeg', '-y', '-err_detect', 'ignore_err', '-i', str(local_720),
    '-vf', 'scale=-2:540',
    '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast',
    '-maxrate', '800k', '-bufsize', '1600k',
    '-c:a', 'copy',
    '-movflags', '+faststart',
    str(local_540)
]
p2 = subprocess.run(cmd2, capture_output=True, text=True)
print("Exit code:", p2.returncode)
if p2.returncode != 0:
    print("Error output:\n", p2.stderr[-500:])
else:
    print("Success! Output size:", local_540.stat().st_size / (1024*1024), "MB")

# Test 3: Re-encode video but let ffmpeg auto-recover (no -c:a copy if it complains about audio packets)
print("\n--- Test 3: Re-encode video and audio, ignore errors ---")
cmd3 = [
    'ffmpeg', '-y', '-err_detect', 'ignore_err', '-i', str(local_720),
    '-vf', 'scale=-2:540',
    '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast',
    '-maxrate', '800k', '-bufsize', '1600k',
    '-c:a', 'aac', '-b:a', '96k',
    '-movflags', '+faststart',
    str(local_540)
]
p3 = subprocess.run(cmd3, capture_output=True, text=True)
print("Exit code:", p3.returncode)
if p3.returncode != 0:
    print("Error output:\n", p3.stderr[-500:])
else:
    print("Success! Output size:", local_540.stat().st_size / (1024*1024), "MB")
