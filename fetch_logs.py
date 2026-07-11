import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

_, stdout, _ = ssh.exec_command('docker logs kingshort-admin-app --tail 50 2>&1')
output = stdout.read().decode('utf-8', 'ignore')

with open('admin_logs.txt', 'w', encoding='utf-8') as f:
    f.write(output)

ssh.close()
