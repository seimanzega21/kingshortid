import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = "SELECT id, title, cover FROM dramas WHERE cover LIKE '%stream.shortlovers.id%' ORDER BY random() LIMIT 50;"
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -t -A -F"|||" -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
lines = stdout.read().decode().strip().split('\n')

urls = []
for line in lines:
    parts = line.split('|||')
    if len(parts) >= 3 and parts[2]:
        urls.append((parts[0], parts[1], parts[2]))

check_script = f"""
import requests
urls = {json.dumps(urls)}
broken = []
ok = 0
for did, title, u in urls:
    try:
        r = requests.head(u, timeout=5)
        if r.status_code == 200:
            ok += 1
        else:
            broken.append((did, title, u, r.status_code))
    except Exception as e:
        broken.append((did, title, u, str(e)))

print(f"Sample 50 check: {{ok}} OK, {{len(broken)}} broken")
for b in broken:
    print("  BROKEN:", b)
"""

with open('scratch/temp_check.py', 'w', encoding='utf-8') as f:
    f.write(check_script)

ssh.close()
