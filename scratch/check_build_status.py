import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Check active docker builds or container creations
        stdin, stdout, stderr = ssh.exec_command('docker ps -a --format "{{.ID}} | {{.Names}} | {{.Image}} | {{.Status}} | {{.CreatedAt}}" | sort -r -k 5 | head -n 15')
        print("\n--- ACTIVE OR RECENT DOCKER BUILDS ---")
        print(stdout.read().decode('utf-8'))
        
        # Check docker images sorted by creation date
        stdin, stdout, stderr = ssh.exec_command('docker images --format "{{.Repository}} | {{.Tag}} | {{.CreatedAt}}" | head -n 10')
        print("\n--- LATEST IMAGES ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
