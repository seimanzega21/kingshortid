import paramiko

def disable_fail2ban():
    host = '141.11.160.187'
    user = 'root'
    password = 'Surya123!'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        
        commands = [
            'fail2ban-client unban --all',
            'systemctl stop fail2ban',
            'systemctl disable fail2ban',
            'iptables -F f2b-sshd 2>/dev/null',
            'iptables -X f2b-sshd 2>/dev/null',
            'ufw allow 3002'
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print("OUT:", stdout.read().decode().strip())
            print("ERR:", stderr.read().decode().strip())
            
        print("Successfully disabled fail2ban and cleared rules.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    disable_fail2ban()
