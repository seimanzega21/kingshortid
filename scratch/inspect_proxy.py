import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Look for coolify proxy configurations
        stdin, stdout, stderr = ssh.exec_command('find /data/coolify -name "nginx.conf" -o -name "traefik.yaml" -o -name "caddy.json" -o -name "*caddy*" -o -name "*traefik*"')
        print("\n--- Proxy Configuration Files ---")
        print(stdout.read().decode('utf-8'))
        
        # Let's check Traefik config if Coolify uses Traefik (Coolify v4 uses Traefik/Caddy/Nginx depending on config)
        stdin, stdout, stderr = ssh.exec_command('docker exec -t coolify-proxy cat /etc/nginx/nginx.conf 2>/dev/null || docker exec -t coolify-proxy cat /etc/traefik/traefik.yml 2>/dev/null || docker exec -t coolify-proxy caddy fmt 2>/dev/null')
        print("\n--- Proxy Container Info ---")
        print(stdout.read().decode('utf-8'))
        
        # Let's inspect the files in /data/coolify/proxy/
        stdin, stdout, stderr = ssh.exec_command('ls -R /data/coolify/proxy/ 2>/dev/null')
        print("\n--- Files in /data/coolify/proxy ---")
        print(stdout.read().decode('utf-8'))
        
        # Let's see if we can find any references to "kingshort" or "admin" in /data/coolify/
        stdin, stdout, stderr = ssh.exec_command('grep -rn "kingshort" /data/coolify/ 2>/dev/null | head -n 50')
        print("\n--- Grep kingshort in /data/coolify/ ---")
        print(stdout.read().decode('utf-8'))

        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
