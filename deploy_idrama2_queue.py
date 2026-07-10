# -*- coding: utf-8 -*-
import paramiko
import os

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    print("Uploading ingest_idrama2_queue_vps.py to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        sftp = ssh.open_sftp()
        sftp.put('d:/kingshortid/ingest_idrama2_queue_vps.py', '/tmp/ingest_idrama2_queue_vps.py')
        sftp.close()
        
        # Stop any existing instances of ingest_idrama2_queue
        print("Stopping any existing instances of ingest_idrama2_queue...")
        ssh.exec_command("pkill -f ingest_idrama2_queue_vps.py")
        
        # Create log file and launch in background
        print("Launching ingest_idrama2_queue_vps.py on VPS in background...")
        ssh.exec_command("touch /var/log/ingest_idrama2_queue.log && chmod 666 /var/log/ingest_idrama2_queue.log")
        ssh.exec_command("nohup python3 -u /tmp/ingest_idrama2_queue_vps.py > /var/log/ingest_idrama2_queue.log 2>&1 &")
        
        print("Launched successfully! Log path: /var/log/ingest_idrama2_queue.log")
        ssh.close()
    except Exception as e:
        print("Error deploying:", e)

if __name__ == '__main__':
    main()
