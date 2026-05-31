import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
ADMIN_CONTAINER = 'zc44ggkksk0oc8oockko44oo-140214505134'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # 1. List files in the root of the app inside the container
        stdin, stdout, stderr = ssh.exec_command(f'docker exec -t {ADMIN_CONTAINER} ls -la')
        print("\n--- Files in Container ---")
        print(stdout.read().decode('utf-8'))
        
        # 2. Check for environment files
        # Let's search if there's any file named .env or containing .env
        stdin, stdout, stderr = ssh.exec_command(f'docker exec -t {ADMIN_CONTAINER} find . -name "*.env*" -o -name ".env*"')
        print("\n--- Environment Files in Container ---")
        print(stdout.read().decode('utf-8'))
        
        # 3. Print the content of any .env file if found
        # We can also check if there is an env file in the working directory (which is usually /app)
        stdin, stdout, stderr = ssh.exec_command(f'docker exec -t {ADMIN_CONTAINER} cat package.json')
        print("\n--- Content of package.json in Container ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
