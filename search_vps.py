import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
    
    # Search for Ratu Tersembunyi Membalas
    cmd = 'curl -s "http://localhost:3000/api/dramas/search?q=Ratu%20Tersembunyi%20Membalas"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("Search response:", stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print("Error:", e)
