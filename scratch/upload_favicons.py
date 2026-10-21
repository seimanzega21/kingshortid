import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\kingshortid\admin\public\favicon.png', '/opt/kingshortid-api/admin/public/favicon.png')
sftp.put(r'D:\kingshortid\admin\public\logo.png', '/opt/kingshortid-api/admin/public/logo.png')
sftp.put(r'D:\kingshortid\admin\src\app\layout.tsx', '/opt/kingshortid-api/admin/src/app/layout.tsx')

# Also copy into container
ssh.exec_command('docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/public/favicon.png')
ssh.exec_command('docker cp /opt/kingshortid-api/admin/public/logo.png kingshort-admin-app:/app/public/logo.png')
ssh.exec_command('docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/public/favicon.ico')

sftp.close()
ssh.close()
print("Files uploaded and copied to container!")
