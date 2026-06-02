import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

keywords = [
    "Dia yang Paling Mencintaiku",
    "Nikah Kilat Sama Bos Lumpuh"
]

for kw in keywords:
    print(f"=== Log for '{kw}' (and subsequent 30 lines) ===")
    cmd = f"grep -A 30 -i '{kw}' /opt/microdrama/scraper.log | head -n 35"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    print(out)
    print("=" * 60)

ssh.close()
