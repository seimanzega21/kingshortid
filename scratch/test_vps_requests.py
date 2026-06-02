import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

url = "https://vidrama.asia/api/microdrama?action=detail&id=1924655580142809089&lang=id"
print(f"Requesting '{url}' via remote Python interpreter...")

# Jalankan script python satu baris di VPS
python_cmd = f"""
python3 -c "
import requests
url = '{url}'
try:
    r = requests.get(url, timeout=30)
    print('HTTP Status:', r.status_code)
    print('Response Headers:', dict(r.headers))
    if r.status_code == 200:
        data = r.json()
        print('Keys:', list(data.keys()))
        print('Episodes count:', len(data.get('episodes', [])))
    else:
        print('Response Text:', r.text[:200])
except Exception as e:
    print('Error:', e)
"
"""

stdin, stdout, stderr = ssh.exec_command(python_cmd)
print("PYTHON OUTPUT:")
print(stdout.read().decode())
print("PYTHON ERRORS:")
print(stderr.read().decode())

ssh.close()
