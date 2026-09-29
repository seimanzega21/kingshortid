import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)
ssh.exec_command("pkill -f ingest_mengusik_raja_semesta_vps.py")
ssh.close()
