import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

cmd = """
docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/static/media/favicon.0b3bf435.ico
docker restart kingshort-admin-app
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
