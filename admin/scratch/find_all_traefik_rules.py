import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        stdin, stdout, stderr = ssh.exec_command('docker ps -a --format "{{.ID}} | {{.Names}}"')
        containers = stdout.read().decode('utf-8', errors='replace').strip().split('\n')
        
        print("\n--- ALL VPS CONTAINERS TRAEFIK ROUTING RULES ---")
        for line in containers:
            if not line.strip():
                continue
            cid, name = line.split(' | ', 1)
            stdin_i, stdout_i, stderr_i = ssh.exec_command(f'docker inspect {cid}')
            out_i = stdout_i.read().decode('utf-8', errors='replace').strip()
            if not out_i:
                continue
            data = json.loads(out_i)
            if data:
                labels = data[0].get('Config', {}).get('Labels', {})
                traefik_rules = []
                for k, v in labels.items():
                    if 'traefik.http.routers' in k and '.rule' in k:
                        traefik_rules.append(f"{k}: {v}")
                if traefik_rules:
                    print(f"\nContainer: {name} (ID: {cid})")
                    for rule in traefik_rules:
                        print(f"  {rule}")
                        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
