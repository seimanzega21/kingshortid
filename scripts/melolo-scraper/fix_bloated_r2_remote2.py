import paramiko

host = "141.11.160.187"
user = "root"
password = "Surya123!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

py_script = """
import os, boto3
from dotenv import load_dotenv
load_dotenv()
s3 = boto3.client('s3', endpoint_url=os.getenv('R2_ENDPOINT'), aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
bucket = 'shortlovers-media'
for i in range(1, 15):
    try:
        s3.delete_object(Bucket=bucket, Key=f'vidrama/microdrama/bangkit-dari-dosa-palsu/ep{i:03d}.mp4')
        s3.delete_object(Bucket=bucket, Key=f'vidrama/microdrama/bangkit-dari-dosa-palsu/ep{i:03d}_540p.mp4')
    except: pass
print('DELETION DONE!')
"""

stdin, stdout, stderr = ssh.exec_command(f'cd /opt/microdrama && source venv/bin/activate && python3 -c "{py_script}"')
print("STDOUT:")
for line in stdout.readlines():
    print(line.strip())

# Restart the scraper so it sees the missing ones
ssh.exec_command("screen -X -S microdrama quit || true")
ssh.exec_command("cd /opt/microdrama && rm -f scraper.log && screen -dmS microdrama bash -c 'source venv/bin/activate && python3 vidrama_microdrama_v4.py --limit 400 > scraper.log 2>&1'")

ssh.close()
