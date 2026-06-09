import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def deploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)
        print("Connected successfully.")
        
        commands = [
            "cd /opt/kingshortid-api",
            "git pull origin main",
            "cd cf-backend",
            "docker compose build --no-cache",
            "docker compose up -d",
            "docker compose ps"
        ]
        
        full_command = " && ".join(commands)
        print(f"Executing: {full_command}")
        
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
        # Stream the output to console in real-time
        for line in stdout:
            print(line.strip())
            
        err = stderr.read().decode('utf-8')
        if err:
            print("Errors/Warnings during command execution:", err, file=sys.stderr)
            
        ssh.close()
        print("Deployment session completed.")
    except Exception as e:
        print("Deployment failed:", e)

if __name__ == "__main__":
    deploy()
