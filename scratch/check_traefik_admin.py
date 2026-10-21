import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshort-admin-app --format "{{json .Config.Labels}}"')
print("=== LABELS OF kingshort-admin-app ===")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshortid-api --format "{{json .Config.Labels}}"')
print("=== LABELS OF kingshortid-api ===")
print(stdout.read().decode())

ssh.close()
