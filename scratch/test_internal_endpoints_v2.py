import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Test kingshortid-api via docker inspect/curl
        # We can curl using their container IPs in the coolify network
        # kingshortid-api IP is 10.0.1.26
        # zc44ggkksk0oc8oockko44oo IP is 10.0.1.30
        
        print("\n--- Test kingshortid-api (10.0.1.26) ---")
        stdin, stdout, stderr = ssh.exec_command('curl -I http://10.0.1.26:3000/')
        print(stdout.read().decode('utf-8'))
        stdin, stdout, stderr = ssh.exec_command('curl -s http://10.0.1.26:3000/ | head -n 10')
        print(stdout.read().decode('utf-8'))
        
        print("\n--- Test zc44ggkksk0oc8oockko44oo (10.0.1.30) ---")
        stdin, stdout, stderr = ssh.exec_command('curl -I http://10.0.1.30:3000/')
        print(stdout.read().decode('utf-8'))
        stdin, stdout, stderr = ssh.exec_command('curl -s http://10.0.1.30:3000/ | head -n 10')
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
