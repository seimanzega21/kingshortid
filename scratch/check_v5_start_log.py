import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

print("Reading first 180 lines of scraper.log from VPS...\n")
stdin, stdout, stderr = ssh.exec_command("head -n 180 /opt/microdrama/scraper.log")
print(stdout.read().decode())

ssh.close()
