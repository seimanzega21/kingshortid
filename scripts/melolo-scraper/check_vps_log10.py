import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

setup_cmd = """
cd /opt/microdrama
rm -f scraper.log
screen -dmS microdrama bash -c "source venv/bin/activate && python3 vidrama_microdrama_v4.py --limit 400 > scraper.log 2>&1"
"""
stdin, stdout, stderr = ssh.exec_command(setup_cmd)
print("DEPLOYS DONE")

ssh.close()
