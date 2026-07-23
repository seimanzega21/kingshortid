import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3000/api/dramas/qi78j2pyz6vjey9r0aded2zv/episodes?includeInactive=true')
out = stdout.read().decode()
data = json.loads(out)
for ep in data:
    if ep['episodeNumber'] in [1, 2, 3, 4, 5, 6, 7, 8]:
        print(f"Ep {ep['episodeNumber']}: id={ep['id']} isActive={ep['isActive']}")
