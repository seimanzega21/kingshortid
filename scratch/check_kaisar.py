import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:3000/api/dramas?search=Kaisar&limit=100"')
out = stdout.read().decode()
data = json.loads(out)
for d in data.get('dramas', []):
    print(d['id'], d['title'], d['isActive'], d['totalEpisodes'])
