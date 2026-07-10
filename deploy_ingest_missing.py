# -*- coding: utf-8 -*-
import paramiko
import os

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    print("Uploading ingest_missing_v2.py to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        sftp = ssh.open_sftp()
        sftp.put('d:/kingshortid/ingest_missing_v2.py', '/tmp/ingest_missing_v2.py')
        sftp.close()
        
        # Stop any existing missing ingestions
        print("Stopping any existing instances of ingest_missing_v2...")
        ssh.exec_command("pkill -f ingest_missing_v2.py")
        
        # Create log file and launch in background
        print("Launching ingest_missing_v2.py on VPS in background...")
        ssh.exec_command("touch /var/log/ingest_missing_v2.log && chmod 666 /var/log/ingest_missing_v2.log")
        ssh.exec_command("nohup python3 -u /tmp/ingest_missing_v2.py > /var/log/ingest_missing_v2.log 2>&1 &")
        
        print("Launched successfully! Log path: /var/log/ingest_missing_v2.log")
        ssh.close()
    except Exception as e:
        print("Error deploying:", e)

if __name__ == '__main__':
    main()
