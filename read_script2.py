import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)
stdin, stdout, stderr = ssh.exec_command('head -n 50 /root/ingest_netshort_vps.py')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
