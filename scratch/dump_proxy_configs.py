import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # List all files and output their content
        stdin, stdout, stderr = ssh.exec_command('ls /data/coolify/proxy/dynamic/')
        files = stdout.read().decode('utf-8').splitlines()
        
        for file in files:
            file = file.strip()
            if not file:
                continue
            print(f"\n--- File: {file} ---")
            stdin, stdout, stderr = ssh.exec_command(f'cat /data/coolify/proxy/dynamic/{file}')
            print(stdout.read().decode('utf-8'))
            
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
