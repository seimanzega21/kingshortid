import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print("Connected successfully.")
    
    print("\n--- PROCESS STATUS ---")
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[i]ngest_melolov3_queue_vps.py"')
    out = stdout.read().decode().strip()
    if out:
        print(out)
    else:
        print("No ingestion process is currently running.")
        
    print("\n--- RECENT LOGS (/var/log/ingest_batch_24.log) ---")
    stdin, stdout, stderr = ssh.exec_command('tail -n 20 /var/log/ingest_batch_24.log')
    print(stdout.read().decode())
    
except Exception as e:
    print("SSH Connection failed:", e)
finally:
    ssh.close()
