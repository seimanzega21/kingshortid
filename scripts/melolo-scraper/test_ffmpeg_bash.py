import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

bash_script = """#!/bin/bash
mkdir -p /tmp/fftest
cd /tmp/fftest
head -c 10000 /dev/urandom > raw.mp4
ffmpeg -y -i raw.mp4 -c:v libx264 -preset ultrafast -crf 28 -movflags +faststart -pix_fmt yuv420p -c:a aac -b:a 96k -ac 2 opt.mp4 > ff.log 2>&1
echo "Exit code: $?" >> ff.log
echo "Output exists: $(ls opt.mp4 2>/dev/null)" >> ff.log
cat ff.log
"""

with open("test.sh", "w") as f:
    f.write(bash_script)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    sftp = ssh.open_sftp()
    sftp.put("test.sh", "/tmp/test.sh")
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("bash /tmp/test.sh")
    print("--- BASH REPRO ---")
    print(stdout.read().decode())
    
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
