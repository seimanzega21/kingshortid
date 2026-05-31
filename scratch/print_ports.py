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
        
        containers = ['kingshortid-api', 'zc44ggkksk0oc8oockko44oo-140214505134']
        for name in containers:
            stdin, stdout, stderr = ssh.exec_command(f'docker inspect {name}')
            out = stdout.read().decode('utf-8').strip()
            if out:
                data = json.loads(out)[0]
                print(f"\n--- Env of {name} ---")
                for var in data.get('Config', {}).get('Env', []):
                    if "PORT" in var or "HOST" in var:
                        print("  ", var)
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
