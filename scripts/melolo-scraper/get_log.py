import paramiko
import os

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    sftp = ssh.open_sftp()
    sftp.get("/opt/microdrama/scraper.log", "vps_scraper.log")
    sftp.close()
    print("Log downloaded successfully.")
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
