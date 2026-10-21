import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshort-admin-app')
data = json.loads(stdout.read().decode())[0]

print("=== IMAGE ===")
print(data.get('Config', {}).get('Image'))

print("=== ENV ===")
for e in data.get('Config', {}).get('Env', []):
    print(" ", e)

print("=== NETWORK / IP ===")
for net_name, net_val in data.get('NetworkSettings', {}).get('Networks', {}).items():
    print(f"  {net_name}: {net_val.get('IPAddress')}")

ssh.close()
