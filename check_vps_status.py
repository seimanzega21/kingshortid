import paramiko
import json

if not hasattr(paramiko, 'DSSKey'):
    try:
        paramiko.DSSKey = paramiko.dsskey.DSSKey
    except Exception:
        class FakeDSSKey:
            pass
        paramiko.DSSKey = FakeDSSKey

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SSH_HOST, port=22, username=SSH_USER, password=SSH_PASS, timeout=15)

print("\n=== TEST Admin Panel /api/dashboard FROM INSIDE VPS ===")
cmd = f'curl -s -m 15 http://localhost:3002/api/dashboard'
stdin, stdout, stderr = client.exec_command(cmd)
raw = stdout.read().decode(errors='replace')

try:
    data = json.loads(raw)
    print("SUCCESS: JSON Dashboard Output:")
    print(json.dumps(data, indent=2)[:500] + "...\n(TRUNCATED)")
except Exception as e:
    print("FAILED TO PARSE JSON:")
    print(raw)

client.close()
