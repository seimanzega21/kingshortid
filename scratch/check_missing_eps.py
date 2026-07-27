import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print("=== CHECKING MISSING EPISODES IN LOG ===")
    
    # Check for missing episodes
    cmd = '''
    echo "Logs for Ep 10:"
    grep -i "Episode 10/" /var/log/ingest_nikah_habis_turun_gunung.log -A 5
    echo "---"
    echo "Logs for Ep 22:"
    grep -i "Episode 22/" /var/log/ingest_nikah_habis_turun_gunung.log -A 5
    echo "---"
    echo "Logs for Ep 38:"
    grep -i "Episode 38/" /var/log/ingest_nikah_habis_turun_gunung.log -A 5
    echo "---"
    echo "Any Error/Failed/Exception in logs:"
    grep -i -E "error|fail|exception" /var/log/ingest_nikah_habis_turun_gunung.log | tail -n 20
    '''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
except Exception as e:
    print("SSH Connection failed:", e)
finally:
    ssh.close()
