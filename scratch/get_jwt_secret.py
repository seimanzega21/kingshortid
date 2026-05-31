import paramiko
import json

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command('docker inspect kingshortid-api')
        out = stdout.read().decode('utf-8').strip()
        if out:
            data = json.loads(out)[0]
            env_vars = data.get('Config', {}).get('Env', [])
            for var in env_vars:
                if var.startswith("JWT_SECRET="):
                    print(var)
                if var.startswith("DATABASE_URL="):
                    print(var)
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
