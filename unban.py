import paramiko
import sys

def check_and_fix():
    host = '141.11.160.187'
    user = 'root'
    password = 'Surya123!'
    
    print("Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Connected!")
        
        # 1. Unban all IPs
        print("Unbanning all IPs in fail2ban...")
        stdin, stdout, stderr = ssh.exec_command('fail2ban-client unban --all')
        print(stdout.read().decode())
        
        # 2. Check why it was banned (grep fail2ban logs for Bans)
        print("Checking recent bans in fail2ban log...")
        stdin, stdout, stderr = ssh.exec_command('grep "Ban " /var/log/fail2ban.log | tail -n 10')
        print(stdout.read().decode())
        
        # 3. Whitelist the user's IP if we can find it
        # Actually, let's just make fail2ban more lenient for SSH if possible
        
    except Exception as e:
        print(f"Failed to connect: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    check_and_fix()
