import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker exec -i coolify-proxy wget -qO- http://kingshort-admin-app:3000/login | head -n 5')
print("Output from coolify-proxy to kingshort-admin-app:")
print(stdout.read().decode())
print("Error:", stderr.read().decode())

ssh.close()
