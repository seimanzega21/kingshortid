import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("ls -la /opt/microdrama > /tmp/ls.txt && cat /tmp/ls.txt")
print("LS:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("cat /opt/microdrama/scraper.log | tr '\\r' '\\n' | tail -n 10")
print("SCRAPER LOG:")
print(stdout.read().decode())

ssh.close()
