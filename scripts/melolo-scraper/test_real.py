
import requests
import subprocess
from pathlib import Path

url = "https://reeltv.janzhoutec.com/ooO5xLSTIAAOUEGnQ0SIWM5ZgAKApw0nfDxGVp"
raw = Path("/tmp/test_raw.mp4")
opt = Path("/tmp/test_opt.mp4")

if not raw.exists():
    print("Downloading real video...")
    r = requests.get(url, stream=True)
    with open(raw, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print("Downloaded:", raw.stat().st_size, "bytes")

cmd = [
    "ffmpeg", "-y", "-i", str(raw),
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "28",
    "-movflags", "+faststart",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "96k", "-ac", "2",
    str(opt)
]
print("Running ffmpeg...")
res = subprocess.run(cmd, capture_output=True)
print("Return code:", res.returncode)
print("Opt exists:", opt.exists())
if opt.exists():
    print("Opt size:", opt.stat().st_size)
print("Stderr head/tail:")
err = res.stderr.decode('utf-8', errors='replace')
print(err[:200])
print("...")
print(err[-200:])
