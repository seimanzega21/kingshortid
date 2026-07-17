# -*- coding: utf-8 -*-
import paramiko
import os

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    print("Uploading ingest_dramawavev2_queue_vps.py to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        sftp = ssh.open_sftp()
        sftp.put('d:/kingshortid/ingest_dramawavev2_queue_vps.py', '/tmp/ingest_dramawavev2_queue_vps.py')
        sftp.close()
        
        # Kill the single-drama process and any previous queues
        print("Stopping existing single-drama and queue processes on VPS...")
        ssh.exec_command("pkill -f ingest_nikah_habis_turun_gunung.py")
        ssh.exec_command("pkill -f ingest_dramawavev2_queue_vps.py")
        
        # Launch process in background (reusing log file path)
        print("Launching ingest_dramawavev2_queue_vps.py on VPS in background...")
        ssh.exec_command("touch /var/log/ingest_nikah_habis_turun_gunung.log && chmod 666 /var/log/ingest_nikah_habis_turun_gunung.log")
        ssh.exec_command("nohup python3 -u /tmp/ingest_dramawavev2_queue_vps.py > /var/log/ingest_nikah_habis_turun_gunung.log 2>&1 &")
        
        print("Launched successfully! Log path: /var/log/ingest_nikah_habis_turun_gunung.log")
        ssh.close()
    except Exception as e:
        print("Error deploying:", e)

if __name__ == '__main__':
    main()
