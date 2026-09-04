import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

stdin, stdout, stderr = ssh.exec_command('git -C /opt/kingshortid-api log -n 1 -- cf-backend/src/middleware/auth.ts')
print("VPS auth.ts git log:")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('grep -n "365d" /opt/kingshortid-api/cf-backend/src/middleware/auth.ts')
print("VPS auth.ts 365d grep:")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshortid-api --format "{{.State.StartedAt}}"')
print("kingshortid-api container started at:")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('docker exec kingshortid-api grep -n "365d" /app/src/middleware/auth.ts 2>/dev/null || docker exec kingshortid-api grep -n "365d" /app/dist/middleware/auth.js 2>/dev/null || docker exec kingshortid-api ls -la /app')
print("Container file inspection:")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
