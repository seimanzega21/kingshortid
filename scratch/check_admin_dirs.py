import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('ls -la /root/kingshort-admin /opt/kingshortid-api/admin')
print(stdout.read().decode())

ssh.close()
