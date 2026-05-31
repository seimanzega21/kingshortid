import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Check coolify logs for recent actions
        stdin, stdout, stderr = ssh.exec_command('docker logs --tail 100 coolify')
        print("\n--- COOLIFY LOGS ---")
        content = stdout.read().decode('utf-8', errors='ignore')
        ascii_content = content.encode('ascii', 'ignore').decode('ascii')
        print(ascii_content)
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
