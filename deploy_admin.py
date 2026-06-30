import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

# Env variables for docker container
ENV_VARS = {
    "DATABASE_URL": "postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@supabase-db-og8gwooogk480gcws0o84ssc:5432/postgres",
    "JWT_SECRET": "MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13",
    "ADMIN_API_KEY": "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14",
    "BACKEND_URL": "http://kingshortid-api:3000/api",
    "R2_ENDPOINT": "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com",
    "R2_ACCESS_KEY_ID": "07c99c897986ea52703c1285308d5e2c",
    "R2_SECRET_ACCESS_KEY": "44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44",
    "R2_BUCKET_NAME": "shortlovers",
    "R2_PUBLIC_URL": "https://stream.shortlovers.id",
    "NODE_ENV": "production",
    "NEXT_TELEMETRY_DISABLED": "1"
}

def run_command_stream(ssh, cmd):
    print(f"\n--- Running Command: {cmd} ---")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    
    # Read output line by line as it is generated
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            rl = stdout.readline()
            if rl:
                print(rl.strip('\r\n'))
        time.sleep(0.1)
        
    # Read remaining
    for line in stdout:
        print(line.strip('\r\n'))
        
    exit_code = stdout.channel.recv_exit_status()
    print(f"Command exited with status code: {exit_code}")
    return exit_code

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        # 0. Update repo to main branch and reset
        update_cmd = "cd /root/kingshort-admin && git fetch origin && git checkout main && git reset --hard origin/main"
        exit_code = run_command_stream(ssh, update_cmd)
        if exit_code != 0:
            print("❌ Git update/checkout failed!")
            ssh.close()
            return

        # 1. Build the Docker image
        build_cmd = "docker build -t kingshort-admin /root/kingshort-admin/admin"
        exit_code = run_command_stream(ssh, build_cmd)
        if exit_code != 0:
            print("❌ Docker build failed!")
            ssh.close()
            return
            
        # 2. Stop and remove existing container if it exists
        print("\nStopping existing admin container...")
        ssh.exec_command("docker rm -f kingshort-admin-app")
        time.sleep(2)
        
        # 3. Construct run command
        env_args = " ".join([f'-e {k}="{v}"' for k, v in ENV_VARS.items()])
        run_cmd = (
            f"docker run -d "
            f"--name kingshort-admin-app "
            f"--network og8gwooogk480gcws0o84ssc "
            f"--restart always "
            f"-p 3002:3000 "
            f"{env_args} "
            f"kingshort-admin"
        )
        
        print("\nStarting the admin panel container...")
        # We don't use stream here, we just run it and check if it started successfully
        stdin, stdout, stderr = ssh.exec_command(run_cmd)
        run_out = stdout.read().decode('utf-8').strip()
        run_err = stderr.read().decode('utf-8').strip()
        
        if run_out:
            print(f"Container started. ID: {run_out}")
        if run_err:
            print(f"Container start stderr: {run_err}")
            
        # 4. Check if container is running
        print("\nVerifying container status...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -f name=kingshort-admin-app")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
        print("Done.")
    except Exception as e:
        print("Error deploying Admin Panel:", e)

if __name__ == "__main__":
    main()
