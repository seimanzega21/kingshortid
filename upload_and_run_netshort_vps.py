# -*- coding: utf-8 -*-
"""
Upload and run ingest_netshort_vps.py on VPS in the background
"""
import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Uploading
        sftp = ssh.open_sftp()
        print("Uploading ingest_netshort_vps.py to VPS...")
        sftp.put('d:/kingshortid/ingest_netshort_vps.py', '/root/ingest_netshort_vps.py')
        sftp.close()
        
        # Kill any existing ones
        print("Stopping any existing netshort pipelines on VPS...")
        ssh.exec_command("pkill -f ingest_netshort_vps.py")
        
        # Run in background
        print("Launching ingest_netshort_vps.py in background on VPS...")
        cmd = "nohup python3 -u /root/ingest_netshort_vps.py > /var/log/ingest_netshort.log 2>&1 &"
        ssh.exec_command(cmd)
        
        print("Done!")
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
