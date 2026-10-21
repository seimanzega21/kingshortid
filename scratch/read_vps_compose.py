import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('cat /opt/kingshortid-api/cf-backend/docker-compose.yml')
content = stdout.read().decode()
print("=== CURRENT DOCKER-COMPOSE.YML ===")
print(content)

ssh.close()
