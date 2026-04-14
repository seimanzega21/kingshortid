import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = ssh.exec_command("grep -oP '\] \K.*' /opt/microdrama/scraper.log | grep -v 'Ep ' | head -n 30")
    print(stdout.read().decode())
    
    print("\n--- Recent Log Activity ---")
    stdin, stdout, stderr = ssh.exec_command("tail -n 25 /opt/microdrama/scraper.log")
    print(stdout.read().decode())
except Exception as e:
    print("Failed or Error:", e)
finally:
    ssh.close()
