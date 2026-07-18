import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

cmd = "cd /root/kingshort-admin && python3 ingest_dramawavev2_queue_vps.py"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)

print(f"Running command on VPS: {cmd}")
stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)

for line in iter(stdout.readline, ""):
    print(line, end="")

exit_code = stdout.channel.recv_exit_status()
print(f"Exit code: {exit_code}")
ssh.close()
