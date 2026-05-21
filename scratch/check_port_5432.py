import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Run netstat or ss to find port 5432
        stdin, stdout, stderr = ssh.exec_command('ss -tulnp | grep 5432')
        print("\n--- Ports listening on 5432 ---")
        print(stdout.read().decode('utf-8'))
        print(stderr.read().decode('utf-8'))
        
        # Let's inspect container lggcc4oso8wsk8w0occw4gwc to see what it is
        stdin, stdout, stderr = ssh.exec_command('docker inspect lggcc4oso8wsk8w0occw4gwc')
        inspect_data = stdout.read().decode('utf-8')
        if inspect_data:
            import json
            data = json.loads(inspect_data)
            print("\n--- Container lggcc4oso8wsk8w0occw4gwc Details ---")
            print(f"Name: {data[0].get('Name')}")
            print(f"Image: {data[0].get('Config', {}).get('Image')}")
            print(f"Ports: {data[0].get('NetworkSettings', {}).get('Ports')}")
            env = data[0].get('Config', {}).get('Env', [])
            print("Env keys:")
            for e in env:
                print(f"  {e.split('=', 1)[0]}")
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
