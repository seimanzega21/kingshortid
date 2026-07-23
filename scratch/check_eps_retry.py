import paramiko, json, time
for i in range(5):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3000/api/dramas/qi78j2pyz6vjey9r0aded2zv/episodes?includeInactive=true')
        out = stdout.read().decode()
        data = json.loads(out)
        for ep in data:
            if ep['episodeNumber'] in [1, 2, 3, 4, 5]:
                print(f"Ep {ep['episodeNumber']}: id={ep['id']} isActive={ep['isActive']}")
        break
    except Exception as e:
        print("Error:", e)
        time.sleep(2)
