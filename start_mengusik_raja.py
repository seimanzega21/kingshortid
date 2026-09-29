import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
    
    # Run in background
    print("Launching ingest_mengusik_raja_semesta_vps.py in background on VPS...")
    cmd = "nohup python3 -u /root/ingest_mengusik_raja_semesta_vps.py > /var/log/ingest_mengusik_raja.log 2>&1 &"
    ssh.exec_command(cmd)
    
    print("Started!")
    ssh.close()
except Exception as e:
    print("Error:", e)
