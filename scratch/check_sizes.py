import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

cmd = """
docker exec kingshort-admin-app ls -lh /app/.next/server/app/favicon.ico.body
docker exec kingshort-admin-app ls -lh /app/.next/static/media/favicon.0b3bf435.ico
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())

ssh.close()
