import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshort-admin-app --format "{{json .HostConfig}}"')
data = json.loads(stdout.read().decode())
print("PortBindings:", data.get('PortBindings'))
print("RestartPolicy:", data.get('RestartPolicy'))
print("NetworkMode:", data.get('NetworkMode'))

stdin, stdout, stderr = ssh.exec_command('history | grep -i admin-app | tail -n 10')
print("History:", stdout.read().decode())

ssh.close()
