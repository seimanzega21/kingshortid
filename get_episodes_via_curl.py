# -*- coding: utf-8 -*-
import paramiko
import json

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3001/api/dramas/vfwqqc61f6scykh037uy5x54/episodes')
        out_bytes = stdout.read()
        out_str = out_bytes.decode('utf-8', errors='ignore')
        
        try:
            data = json.loads(out_str)
            print("Total episodes in DB:", len(data))
            ep_nums = sorted([int(e.get('episodeNumber', 0)) for e in data])
            print("Existing episode numbers:")
            print(ep_nums)
            
            # Print missing episodes up to 78 (since netshortv2 has 78 episodes)
            all_possible = set(range(1, 79))
            existing_set = set(ep_nums)
            missing = sorted(list(all_possible - existing_set))
            print("Missing episode numbers (up to 78):")
            print(missing)
        except Exception as je:
            print("Failed to parse JSON:", je)
            print("Output length:", len(out_str))
            print("Output prefix:", out_str[:500])
            
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
