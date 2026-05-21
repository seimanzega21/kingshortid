import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Test kingshortid-api:3000
        stdin, stdout, stderr = ssh.exec_command('docker exec -t coolify-proxy curl -I http://kingshortid-api:3000/')
        print("\n--- Headers from kingshortid-api:3000 ---")
        print(stdout.read().decode('utf-8'))
        
        stdin, stdout, stderr = ssh.exec_command('docker exec -t coolify-proxy curl -s http://kingshortid-api:3000/ | head -n 20')
        print("\n--- HTML body from kingshortid-api:3000 ---")
        print(stdout.read().decode('utf-8'))
        
        # Test zc44ggkksk0oc8oockko44oo-023620175579:3000
        stdin, stdout, stderr = ssh.exec_command('docker exec -t coolify-proxy curl -I http://zc44ggkksk0oc8oockko44oo-023620175579:3000/')
        print("\n--- Headers from zc44ggkksk0oc8oockko44oo-023620175579:3000 ---")
        print(stdout.read().decode('utf-8'))
        
        stdin, stdout, stderr = ssh.exec_command('docker exec -t coolify-proxy curl -s http://zc44ggkksk0oc8oockko44oo-023620175579:3000/ | head -n 20')
        print("\n--- HTML body from zc44ggkksk0oc8oockko44oo-023620175579:3000 ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
