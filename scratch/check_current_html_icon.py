import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

# Check html of /
stdin, stdout, stderr = ssh.exec_command('curl -s http://kingshort-admin-app:3000 | grep -o "<link[^>]*icon[^>]*>"')
print("Current link icons in html:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('docker inspect kingshort-admin-app --format "{{.Created}}"')
print("Container Created at:", stdout.read().decode())

ssh.close()
