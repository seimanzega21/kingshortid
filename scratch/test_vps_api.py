import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

url = "https://vidrama.asia/api/microdrama?action=detail&id=1924655580142809089&lang=id"
print(f"Requesting '{url}' from remote VPS using curl...")

# Gunakan curl dengan silent mode untuk melihat status code dan 200 karakter pertama
cmd = f"curl -i -s '{url}' | head -n 25"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("CURL OUTPUT:")
print(stdout.read().decode())

ssh.close()
