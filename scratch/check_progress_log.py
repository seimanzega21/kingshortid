import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print("=== LOG PROGRESS ===")
    
    stdin, stdout, stderr = ssh.exec_command('grep -A 2 -B 2 "Registered" /var/log/ingest_nikah_habis_turun_gunung.log | tail -n 15')
    print(stdout.read().decode())
except Exception as e:
    print("Gagal connect SSH:", e)
finally:
    ssh.close()
