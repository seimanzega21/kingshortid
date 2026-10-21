import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('curl -s http://kingshort-admin-app:3000 | grep -o "favicon[^\"\' >]*"')
print("Favicon occurrences:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('docker exec kingshort-admin-app find /app -name "*favicon*"')
print("Favicon files in container:")
print(stdout.read().decode())

ssh.close()
