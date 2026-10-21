import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker exec kingshort-admin-app ls -l /app/.next/server/app/favicon.ico*')
print("Docker server favicon files:")
print(stdout.read().decode())

ssh.close()
