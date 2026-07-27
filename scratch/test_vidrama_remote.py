import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    
    script = """
import requests
import urllib3
urllib3.disable_warnings()
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://vidrama.asia/'}
r_det = requests.get('https://vidrama.asia/api/melolov3/series?id=7626247544758078517&lang=id', headers=HEADERS, verify=False, timeout=10)
r_vid = requests.get('https://vidrama.asia/api/melolov3/multi-video?id=7626247544758078517&lang=id', headers=HEADERS, verify=False, timeout=10)
print('det ok:', r_det.ok, 'vid ok:', r_vid.ok)
if r_det.ok:
    print('det json keys:', r_det.json().keys())
if r_vid.ok:
    print('vid json keys:', r_vid.json().keys())
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_vidrama.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_vidrama.py')
    print(stdout.read().decode())
    print(stderr.read().decode())
except Exception as e:
    print('Failed:', e)
finally:
    ssh.close()
