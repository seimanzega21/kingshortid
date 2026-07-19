import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)

LOG = '/var/log/ingest_rahasia_hasil_laut_langka.log'
stdin, stdout, stderr = ssh.exec_command(f'tail -30 {LOG}')
print(stdout.read().decode())

# Cek apakah masih running
stdin, stdout, stderr = ssh.exec_command('pgrep -la python3 | grep ingest_melolov3')
proc = stdout.read().decode().strip()
print('Process:', proc if proc else '(sudah selesai)')

ssh.close()
