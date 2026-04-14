import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = ssh.exec_command("cat /opt/microdrama/scraper.log | wc -l")
    lines = stdout.read().decode().strip()
    print("Lines in log:", lines)
    
    stdin, stdout, stderr = ssh.exec_command("tail -n 25 /opt/microdrama/scraper.log")
    print(stdout.read().decode())
except Exception as e:
    print("Failed or Error:", e)
finally:
    ssh.close()
