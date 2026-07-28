import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print('Checking running dramawavev2 scripts...')
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep ingest_dramawavev2_queue_vps.py | grep -v grep')
    print(stdout.read().decode())
    print('Checking log for Ep 51 error...')
    stdin, stdout, stderr = ssh.exec_command('grep -i "Episode 51/100" /var/log/ingest_nikah_habis_turun_gunung.log -A 5')
    print(stdout.read().decode())
except Exception as e:
    print('Failed:', e)
finally:
    ssh.close()
