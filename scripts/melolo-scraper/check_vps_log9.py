import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("cd /opt/microdrama && source venv/bin/activate && python3 vidrama_microdrama_v4.py --limit 4")
print("STDOUT:")
for line in stdout.readlines():
    print(line.strip())

print("STDERR:")
for line in stderr.readlines():
    print(line.strip())

ssh.close()
