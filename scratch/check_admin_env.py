import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshort-admin-app --format "{{json .Config.Env}}"')
envs = json.loads(stdout.read().decode())
print("=== kingshort-admin-app ENVS ===")
for e in envs:
    print(" ", e)

ssh.close()
