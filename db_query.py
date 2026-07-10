# -*- coding: utf-8 -*-
import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Connect to DB and run activation SQLs
        cmd = """docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "
            UPDATE dramas SET is_active = true WHERE id = 'wfwqgc6f6scykh032uy5x554';
            UPDATE episodes SET is_active = true WHERE drama_id = 'wfwqgc6f6scykh032uy5x554';
        " """
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("STDOUT:")
        print(stdout.read().decode('utf-8'))
        print("STDERR:")
        print(stderr.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
