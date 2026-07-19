"""Upload ingest_melolov3_queue_vps.py ke VPS dan jalankan"""
import paramiko
import time

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

LOCAL_SCRIPT = r'd:\kingshortid\ingest_melolov3_queue_vps.py'
REMOTE_SCRIPT = '/root/kingshort-admin/ingest_melolov3_queue_vps.py'
LOG_FILE = '/var/log/ingest_rahasia_hasil_laut_langka.log'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)

# Upload script ke VPS
sftp = ssh.open_sftp()
sftp.put(LOCAL_SCRIPT, REMOTE_SCRIPT)
sftp.close()
print(f'✅ Uploaded: {REMOTE_SCRIPT}')

# Kill any existing instance
ssh.exec_command('pkill -f ingest_melolov3_queue_vps.py 2>/dev/null || true')
time.sleep(1)

# Jalankan di background
cmd = f'nohup python3 -u {REMOTE_SCRIPT} > {LOG_FILE} 2>&1 &'
stdin, stdout, stderr = ssh.exec_command(cmd)
time.sleep(2)

# Cek apakah running
stdin, stdout, stderr = ssh.exec_command('pgrep -la python3 | grep ingest_melolov3')
print('Running process:', stdout.read().decode().strip())

# Tampilkan 5 baris pertama log
time.sleep(3)
stdin, stdout, stderr = ssh.exec_command(f'head -20 {LOG_FILE} 2>/dev/null || echo "(log belum ada)"')
print('Log preview:')
print(stdout.read().decode())

print(f'\nLog file: {LOG_FILE}')
ssh.close()
