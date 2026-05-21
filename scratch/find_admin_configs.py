import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
UUID = 'l40cccg8ck4g48w8kgss8ggk'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # List files in the application's configuration directory in Coolify
        stdin, stdout, stderr = ssh.exec_command(f'ls -la /data/coolify/applications/{UUID}/')
        print(f"\n--- Files in /data/coolify/applications/{UUID}/ ---")
        print(stdout.read().decode('utf-8'))
        
        # Check compose file
        stdin, stdout, stderr = ssh.exec_command(f'cat /data/coolify/applications/{UUID}/docker-compose.yaml')
        print("\n--- docker-compose.yaml ---")
        print(stdout.read().decode('utf-8'))
        
        # Check env file if it exists
        stdin, stdout, stderr = ssh.exec_command(f'cat /data/coolify/applications/{UUID}/.env')
        print("\n--- .env ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
