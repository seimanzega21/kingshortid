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
        
        # Get list of docker networks
        stdin, stdout, stderr = ssh.exec_command('docker network ls --format "{{.Name}}"')
        networks = stdout.read().decode('utf-8').splitlines()
        
        for net in networks:
            net = net.strip()
            if not net or net in ['bridge', 'host', 'none']:
                continue
            print(f"\n================ Network: {net} ================")
            stdin, stdout, stderr = ssh.exec_command(f'docker network inspect {net}')
            data = json.loads(stdout.read().decode('utf-8'))
            if data:
                containers = data[0].get('Containers', {})
                for cid, cinfo in containers.items():
                    print(f"  Container: {cinfo.get('Name')} -> IP: {cinfo.get('IPv4Address')}")
                    
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
