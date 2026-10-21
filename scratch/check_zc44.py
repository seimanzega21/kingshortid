import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker inspect zc44ggkksk0oc8oockko44oo-162623088400 --format "{{json .Config.Labels}}"')
print("=== LABELS OF zc44... ===")
print(stdout.read().decode())

ssh.close()
