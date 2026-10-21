import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

# Replace the Next.js default Vercel icon (favicon.0b3bf435.ico) with KingShort logo
cmd = 'docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/static/media/favicon.0b3bf435.ico'
ssh.exec_command(cmd)

ssh.close()
print("Replaced static favicon with KingShort icon!")
