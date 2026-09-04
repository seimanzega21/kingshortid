import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api bun -e "fetch(\'http://localhost:3000/health\').then(r => r.json()).then(console.log)"')
print("Inside container health test with bun:")
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api bun -e "fetch(\'http://127.0.0.1:3000/health\').then(r => r.json()).then(console.log)"')
print("Inside container health test with 127.0.0.1:")
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
