import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print("=== CHECKING MISSING EPISODES FOR PEMBALASAN SANG IKAN ===")
    
    cmd = '''
    echo "Logs for Ep 42:"
    grep -i "Episode 42/" /var/log/ingest_batch_24.log -A 5
    echo "---"
    echo "Logs for Ep 49:"
    grep -i "Episode 49/" /var/log/ingest_batch_24.log -A 5
    echo "---"
    echo "Logs for Ep 64:"
    grep -i "Episode 64/" /var/log/ingest_batch_24.log -A 5
    echo "---"
    echo "Logs for Ep 65:"
    grep -i "Episode 65/" /var/log/ingest_batch_24.log -A 5
    echo "---"
    echo "Errors in pembalasan-sang-ikan:"
    grep "pembalasan-sang-ikan" /var/log/ingest_batch_24.log | grep -i -E "error|fail|exception" | tail -n 20
    '''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
except Exception as e:
    print("SSH Connection failed:", e)
finally:
    ssh.close()
