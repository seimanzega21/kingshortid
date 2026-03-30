import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = ssh.exec_command("cat /opt/microdrama/scraper.log | grep FFerr | tail -n 5")
    print("--- FFERR IN LOG ---")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command("cat /opt/microdrama/vidrama_microdrama_mp4_v3.py | grep -n FFerr")
    print("--- FFERR IN SOURCE ---")
    print(stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("ls -la /tmp | grep microdrama")
    print("--- /TMP FOLDER ---")
    print(stdout.read().decode())

except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
