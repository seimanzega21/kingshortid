# -*- coding: utf-8 -*-
import paramiko
import os

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    print("Uploading ingest_nikah_habis_turun_gunung.py to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        sftp = ssh.open_sftp()
        sftp.put('d:/kingshortid/ingest_nikah_habis_turun_gunung.py', '/tmp/ingest_nikah_habis_turun_gunung.py')
        sftp.close()
        
        # Kill any existing ones
        ssh.exec_command("pkill -f ingest_nikah_habis_turun_gunung.py")
        
        # Launch process in background
        print("Launching ingest_nikah_habis_turun_gunung.py on VPS in background...")
        ssh.exec_command("touch /var/log/ingest_nikah_habis_turun_gunung.log && chmod 666 /var/log/ingest_nikah_habis_turun_gunung.log")
        ssh.exec_command("nohup python3 -u /tmp/ingest_nikah_habis_turun_gunung.py > /var/log/ingest_nikah_habis_turun_gunung.log 2>&1 &")
        
        print("Launched successfully! Log path: /var/log/ingest_nikah_habis_turun_gunung.log")
        ssh.close()
    except Exception as e:
        print("Error deploying:", e)

if __name__ == '__main__':
    main()
