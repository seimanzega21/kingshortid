import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

# Check the size and type of /app/.next/server/app/favicon.ico.body
stdin, stdout, stderr = ssh.exec_command('ls -l /app/.next/server/app/favicon.ico*')
print("Server favicon files:")
print(stdout.read().decode())

# Overwrite favicon.ico.body with the kingshort icon!
cmd = """
docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/server/app/favicon.ico.body
docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/server/app/favicon.ico
docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/public/favicon.ico
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()

print("Overwritten server app favicon.ico.body!")
ssh.close()
