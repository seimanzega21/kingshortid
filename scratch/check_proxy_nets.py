import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect coolify-proxy --format "{{json .NetworkSettings.Networks}}"')
networks = json.loads(stdout.read().decode())
print("Networks of coolify-proxy:", list(networks.keys()))

ssh.close()
