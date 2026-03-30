import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    
    cmds = [
        "killall screen",
        "pkill -9 -f vidrama",
        "rm -f /opt/microdrama/scraper.log",
        "cd /opt/microdrama && nohup bash -c 'source venv/bin/activate && python3 vidrama_microdrama_mp4_v3.py --limit 200' > scraper.log 2>&1 &",
        "sleep 10",
        "cat /opt/microdrama/scraper.log"
    ]
    
    for cmd in cmds:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
    
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
