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
        
        # 1. docker inspect kingshortid-api
        stdin, stdout, stderr = ssh.exec_command('docker inspect kingshortid-api')
        out = stdout.read().decode('utf-8').strip()
        if out:
            data = json.loads(out)[0]
            print("\n--- Image ID ---")
            print(data.get('Image'))
            print("\n--- State ---")
            print(json.dumps(data.get('State'), indent=2))
            print("\n--- Mounts ---")
            print(json.dumps(data.get('Mounts'), indent=2))
            print("\n--- HostConfig PortBindings ---")
            print(json.dumps(data.get('HostConfig', {}).get('PortBindings'), indent=2))
            print("\n--- NetworkSettings Ports ---")
            print(json.dumps(data.get('NetworkSettings', {}).get('Ports'), indent=2))
            print("\n--- Config Labels ---")
            print(json.dumps(data.get('Config', {}).get('Labels'), indent=2))
        else:
            print("Failed to inspect container:", stderr.read().decode('utf-8'))
            
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
