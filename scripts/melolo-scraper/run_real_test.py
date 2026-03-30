import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

python_script = """
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
"""

with open("test_real.py", "w") as f:
    f.write(python_script)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    sftp = ssh.open_sftp()
    sftp.put("test_real.py", "/tmp/test_real.py")
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/test_real.py")
    print("--- REAL RUN ---")
    print(stdout.read().decode())
    print("--- STDERR ---")
    print(stderr.read().decode())
    
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
