import paramiko
import json
from urllib.parse import urlparse

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

APP_CONTAINERS = [
    'kingshortid-api',
    'zc44ggkksk0oc8oockko44oo-023620175579'
]

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        for container in APP_CONTAINERS:
            stdin, stdout, stderr = ssh.exec_command(f'docker inspect {container}')
            inspect_data = json.loads(stdout.read().decode('utf-8'))
            if inspect_data:
                env_vars = inspect_data[0].get('Config', {}).get('Env', [])
                print(f"\n================ DB CONFIGS FOR {container} ================")
                for var in env_vars:
                    if "DATABASE_URL" in var or "SUPABASE_URL" in var:
                        parts = var.split('=', 1)
                        key, val = parts[0], parts[1]
                        parsed = urlparse(val)
                        print(f"  {key}:")
                        print(f"    Scheme: {parsed.scheme}")
                        print(f"    Host: {parsed.hostname}")
                        print(f"    Port: {parsed.port}")
                        print(f"    Path: {parsed.path}")
                        print(f"    User: {parsed.username}")
                        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
