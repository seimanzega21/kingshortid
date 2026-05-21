import paramiko
import json

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
ADMIN_CONTAINER = 'l40cccg8ck4g48w8kgss8ggk-161926297332'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command(f'docker inspect {ADMIN_CONTAINER}')
        inspect_data = json.loads(stdout.read().decode('utf-8'))
        
        if inspect_data:
            env = inspect_data[0].get('Config', {}).get('Env', [])
            print(f"\n--- ALL Env variables of {ADMIN_CONTAINER} ---")
            for var in env:
                print(var)
                
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
