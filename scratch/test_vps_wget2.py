import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api wget -qO- http://127.0.0.1:3000/health')
print("wget 127.0.0.1 output:")
print(stdout.read().decode('utf-8', errors='ignore'))
print("wget 127.0.0.1 err:")
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
