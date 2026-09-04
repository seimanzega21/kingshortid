import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api wget -qO- http://localhost:3000/health 2>&1 || echo "wget exit code $?"')
print("wget test inside container:")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
