import paramiko
import jwt
import time
import requests

secret = 'MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13'
payload = {
    'id': 'admin',
    'role': 'admin',
    'iat': int(time.time()),
    'exp': int(time.time()) + 3600
}
token = jwt.encode(payload, secret, algorithm='HS256')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

cmd = f"curl -s -H 'Cookie: admin_token={token}' http://localhost:3002/api/analytics"
print("Executing:", cmd)
_, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
