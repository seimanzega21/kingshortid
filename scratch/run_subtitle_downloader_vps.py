"""Upload subtitle_only_downloader.py ke VPS dan jalankan dari sana"""
import paramiko
import os

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

LOCAL_SCRIPT = r'd:\kingshortid\subtitle_only_downloader.py'
REMOTE_SCRIPT = '/root/kingshort-admin/subtitle_only_downloader.py'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)

# Upload script ke VPS
sftp = ssh.open_sftp()
sftp.put(LOCAL_SCRIPT, REMOTE_SCRIPT)
sftp.close()
print(f'✅ Uploaded script to VPS: {REMOTE_SCRIPT}')

# Jalankan script di VPS dengan nohup supaya tidak berhenti jika koneksi putus
cmd = f'cd /root/kingshort-admin && python3 -u {REMOTE_SCRIPT} 2>&1'
print(f'Running: {cmd}')
print()

stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
for line in iter(stdout.readline, ''):
    print(line, end='')

exit_code = stdout.channel.recv_exit_status()
print(f'\nExit code: {exit_code}')
ssh.close()
