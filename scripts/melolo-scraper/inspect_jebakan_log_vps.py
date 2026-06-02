import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

cmd = """
python3 -c "
with open('/opt/microdrama/scraper.log', 'r') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer('Jebakan Sempurna', text)]
for idx, pos in enumerate(matches):
    start = max(0, pos - 200)
    end = min(len(text), pos + 1000)
    print(f'=== MATCH {idx+1} ===')
    print(text[start:end])
    print('='*50)
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
