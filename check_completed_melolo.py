# -*- coding: utf-8 -*-
import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command('grep -n "STARTING INGESTION:" /var/log/ingest_nikah_habis_turun_gunung.log')
        out_bytes = stdout.read()
        out_str = out_bytes.decode('utf-8', errors='ignore')
        cleaned = "".join(c if ord(c) < 128 else '?' for c in out_str)
        print(cleaned)
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
