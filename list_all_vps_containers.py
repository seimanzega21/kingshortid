import paramiko

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
        
        # List all containers with their full details
        stdin, stdout, stderr = ssh.exec_command('docker ps --format "{{.ID}} | {{.Names}} | {{.Image}} | {{.Ports}}"')
        print("\n--- ALL VPS CONTAINERS ---")
        lines = stdout.read().decode('utf-8').strip().split('\n')
        for idx, line in enumerate(lines):
            print(f"{idx+1}. {line}")
            
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
