import paramiko
import json

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
        
        # 1. docker inspect supabase-db-og8gwooogk480gcws0o84ssc
        stdin, stdout, stderr = ssh.exec_command('docker inspect supabase-db-og8gwooogk480gcws0o84ssc')
        inspect_data = json.loads(stdout.read().decode('utf-8'))
        
        if inspect_data:
            ports = inspect_data[0].get('NetworkSettings', {}).get('Ports', {})
            print("\n--- Ports for supabase-db-og8gwooogk480gcws0o84ssc ---")
            print(json.dumps(ports, indent=2))
            
            env = inspect_data[0].get('Config', {}).get('Env', [])
            print("\n--- Env variables ---")
            for var in env:
                if "POSTGRES_PASSWORD" in var or "PASSWORD" in var:
                    parts = var.split('=', 1)
                    print(f"{parts[0]}=***")
                else:
                    print(var)
                    
        # 2. docker ps -a to see all container port mappings directly
        stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\\t{{.Ports}}"')
        print("\n--- Docker PS Port Mapping ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
