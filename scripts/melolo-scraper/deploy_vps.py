import paramiko
import os
import time

host = "141.11.160.187"
user = "root"
password = "Surya123!"

REMOTE_DIR = "/opt/microdrama"
FILES_TO_UPLOAD = ["vidrama_microdrama_v4.py", ".env"]

print(f"Connecting to {host}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=user, password=password, timeout=10)
    print("Connected! Creating directory...")
    ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
    
    # Upload files
    sftp = ssh.open_sftp()
    for file in FILES_TO_UPLOAD:
        if os.path.exists(file):
            print(f"Uploading {file}...")
            sftp.put(file, f"{REMOTE_DIR}/{file}")
        else:
            print(f"WARNING: {file} not found locally.")
    sftp.close()
    
    # Install dependencies and run script in background
    print("Setting up environment on VPS & Starting pipeline...")
    setup_cmd = f"""
    cd {REMOTE_DIR}
    apt-get update -y
    apt-get install -y python3 python3-pip ffmpeg python3-venv
    python3 -m venv venv
    source venv/bin/activate
    pip install requests python-dotenv boto3
    
    # Stop existing if running
    pkill -9 -f python
    pkill -9 -f ffmpeg
    rm -f scraper.log
    
    # Run in background via screen
    screen -dmS microdrama bash -c "source venv/bin/activate && python3 vidrama_microdrama_v4.py --limit 400 > scraper.log 2>&1"
    
    echo "VPS DEPLOYMENT COMPLETE!"
    """
    
    stdin, stdout, stderr = ssh.exec_command(setup_cmd)
    
    # Wait for the echo to ensure it finished starting
    output = stdout.read().decode()
    err = stderr.read().decode()
    print("Output:\n", output)
    if err:
        print("Error/Warnings:\n", err)
        
except Exception as e:
    print("Failed or Error:", e)
finally:
    ssh.close()
