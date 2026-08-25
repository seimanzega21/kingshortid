import paramiko

def check_docker():
    host = '141.11.160.187'
    user = 'root'
    password = 'Surya123!'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        
        # Check docker ps
        stdin, stdout, stderr = ssh.exec_command('docker ps -a')
        output = stdout.read().decode()
        
        # Check logs for admin panel if it exists
        print("DOCKER PS:")
        for line in output.split('\n'):
            if 'admin' in line.lower() or '3002' in line or 'coolify' in line.lower():
                print(line)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    check_docker()
