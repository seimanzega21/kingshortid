import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("screen -ls")
print("SCREENS:")
for line in stdout.readlines():
    print(line.strip())

stdin, stdout, stderr = ssh.exec_command("ps aux | grep -v grep | grep python")
print("PYTHON PROCS:")
for line in stdout.readlines():
    print(line.strip())

ssh.close()
