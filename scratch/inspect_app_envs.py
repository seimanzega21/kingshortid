import paramiko
import json

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

APP_CONTAINERS = [
    'kingshortid-api',
    'l40cccg8ck4g48w8kgss8ggk-161926297332',
    'y048s0s0ck4c8okcg844kg80-125047169715',
    'zc44ggkksk0oc8oockko44oo-023620175579',
    'igswosc0gc44kk8kskos8s4c-103759322714',
    'tk8wkwokwc40ssc0w8k8swgk-135645034477'
]

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        for container in APP_CONTAINERS:
            stdin, stdout, stderr = ssh.exec_command(f'docker inspect {container}')
            out = stdout.read().decode('utf-8').strip()
            if not out:
                print(f"Container {container} not found or inspect failed: {stderr.read().decode('utf-8').strip()}")
                continue
                
            inspect_data = json.loads(out)
            if inspect_data:
                env_vars = inspect_data[0].get('Config', {}).get('Env', [])
                print(f"\n================ ENVIRONMENT OF {container} ================")
                for var in env_vars:
                    # Mask actual secrets but show their keys and structures
                    if any(k in var for k in ["DATABASE", "DB", "URL", "PORT", "SECRET", "KEY"]):
                        parts = var.split('=', 1)
                        if len(parts) == 2:
                            val = parts[1]
                            masked = val[:10] + "..." if len(val) > 10 else "..."
                            print(f"  {parts[0]}={masked}")
                        else:
                            print(f"  {var}")
                    else:
                        print(f"  {var}")
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
