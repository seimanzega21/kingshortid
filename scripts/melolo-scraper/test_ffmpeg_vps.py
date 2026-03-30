import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    
    # We will run a python script on the VPS that reproduces compress_mp4 with a dummy file
    script = """
import subprocess
from pathlib import Path
import os

print(f"OS NAME: {os.name}")
input_mp4 = Path('/tmp/dummy_input.mp4')
output_mp4 = Path('/tmp/dummy_output.mp4')

# Create fake input file of 10KB
with open(input_mp4, 'wb') as f:
    f.write(b'0' * 10000)

cmd = [
    "ffmpeg", "-y", "-i", str(input_mp4),
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "28",
    "-movflags", "+faststart",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "96k", "-ac", "2",
    str(output_mp4)
]

print("Executing:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True)
print("Return code:", res.returncode)
print("Output exists?", output_mp4.exists())
if res.returncode != 0:
    print("STDERR:")
    print(res.stderr.decode('utf-8'))
"""
    stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{script}"')
    
    print("--- REPRO SCRIPT OUTPUT ---")
    print(stdout.read().decode())
    print("--- STDERR ---")
    print(stderr.read().decode())
    
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
