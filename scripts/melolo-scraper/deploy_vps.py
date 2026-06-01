import paramiko
import os
import time

host = "141.11.160.187"
user = "root"
password = "Surya123!"

REMOTE_DIR = "/opt/microdrama"
FILES_TO_UPLOAD = ["vidrama_microdrama_v5.py", ".env"]

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
    python3 -m venv venv
    source venv/bin/activate
    pip install -r <(echo -e "cloudscraper==1.2.71\\npython-slugify==8.0.4\\nboto3==1.34.79")

    # Stop existing screen session directly instead of wildcard pkill
    screen -X -S microdrama quit || true
    
    rm -f scraper.log
    # Run in background via screen
    screen -dmS microdrama bash -c "source venv/bin/activate && python3 vidrama_microdrama_v5.py --limit 400 > scraper.log 2>&1"
    
    echo "VPS Setup & Start OK"
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
