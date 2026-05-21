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
        
        print("\n--- DETECTED KINGSWHORT / SHORTLOVERS / ADMIN CONTAINERS ---")
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
                env_vars = data[0].get('Config', {}).get('Env', [])
                
                # Check labels
                labels_str = json.dumps(labels).lower()
                env_str = json.dumps(env_vars).lower()
                name_lower = name.lower()
                
                is_match = False
                reasons = []
                
                if 'shortlovers' in name_lower or 'kingshort' in name_lower:
                    is_match = True
                    reasons.append("name matches")
                if 'shortlovers' in labels_str or 'kingshort' in labels_str:
                    is_match = True
                    reasons.append("labels match")
                if 'shortlovers' in env_str or 'kingshort' in env_str:
                    is_match = True
                    reasons.append("env matches")
                if 'admin' in name_lower and 'supabase' not in name_lower and 'coolify' not in name_lower:
                    is_match = True
                    reasons.append("admin in name")
                    
                if is_match:
                    print(f"\nContainer: {name} (ID: {cid})")
                    print(f"  Match reasons: {', '.join(reasons)}")
                    print(f"  Image: {data[0].get('Image')}")
                    print(f"  Status: {data[0].get('State', {}).get('Status')}")
                    
                    # Print Traefik/Routing labels
                    traefik_labels = {k: v for k, v in labels.items() if 'traefik' in k}
                    if traefik_labels:
                        print("  Traefik Labels:")
                        for k, v in traefik_labels.items():
                            print(f"    {k}: {v}")
                            
                    # Print important env vars
                    for env in env_vars:
                        if any(x in env for x in ["DATABASE_URL", "URL", "API", "PORT", "ADMIN"]):
                            # Mask password if db url
                            if "DATABASE_URL" in env or "PASSWORD" in env:
                                parts = env.split('=', 1)
                                if len(parts) == 2:
                                    val = parts[1]
                                    masked = val[:5] + "..." if len(val) > 5 else "..."
                                    print(f"    Env: {parts[0]}={masked}")
                            else:
                                print(f"    Env: {env}")
                                
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
