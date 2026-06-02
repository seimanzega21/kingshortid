import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command('tail -n 30 /opt/microdrama/scraper.log')
print("--- SCRAPER LOG TAIL ---")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('grep -n "Processing:" /opt/microdrama/scraper.log')
print("--- ALL DRAPAS PROCESSED SO FAR ---")
print(stdout.read().decode())

ssh.close()
