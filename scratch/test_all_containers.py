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
        
        # We will get all containers on the coolify network and curl them
        stdin, stdout, stderr = ssh.exec_command('docker network inspect coolify')
        data = json.loads(stdout.read().decode('utf-8'))
        
        if data:
            containers = data[0].get('Containers', {})
            for cid, cinfo in containers.items():
                name = cinfo.get('Name')
                ip = cinfo.get('IPv4Address').split('/')[0]
                print(f"\n================ CONTAINER: {name} ({ip}) ================")
                
                # Check ports to see where to curl
                # Let's try port 3000, 80, 8080
                for port in [3000, 80, 8080, 8000]:
                    stdin, stdout, stderr = ssh.exec_command(f'curl -I --connect-timeout 2 http://{ip}:{port}/ 2>/dev/null')
                    headers = stdout.read().decode('utf-8').strip()
                    if headers:
                        print(f"  Port {port} responded:")
                        print(f"    {headers.splitlines()[0]}")
                        # If 200 or similar, grab a snippet of HTML/body
                        stdin, stdout, stderr = ssh.exec_command(f'curl -s --connect-timeout 2 http://{ip}:{port}/ | head -n 5')
                        print(f"    Body snippet: {stdout.read().decode('utf-8').strip()}")
                        break
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
