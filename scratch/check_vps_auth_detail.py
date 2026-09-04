import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api sed -n "55,75p" /app/src/middleware/auth.ts')
print("Container auth.ts lines 55-75:")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
