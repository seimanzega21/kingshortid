import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=15)

def run(cmd):
    print(">>>", cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    if out: print(out)
    if err: print("ERR:", err)

run("docker ps -a --filter name=kingshortid")
run("cd /opt/kingshortid-api && git status")
run("cd /opt/kingshortid-api && git log -n 1 --oneline")
run("curl -s http://localhost:3000/health || echo 'Health check curl failed'")
ssh.close()
