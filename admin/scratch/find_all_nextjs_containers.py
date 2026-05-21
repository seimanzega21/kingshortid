import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to SSH {SSH_USER}@{SSH_HOST}...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("Connected.")
        
        stdin, stdout, stderr = ssh.exec_command('docker ps -a --format "{{.ID}} | {{.Names}}"')
        containers = stdout.read().decode('utf-8', errors='replace').strip().split('\n')
        
        print("\n--- SCANNING ALL CONTAINERS FOR PACKAGE.JSON ---")
        for line in containers:
            if not line.strip():
                continue
            cid, name = line.split(' | ', 1)
            # Try to read package.json
            stdin_pkg, stdout_pkg, stderr_pkg = ssh.exec_command(f'docker exec {cid} cat /app/package.json')
            pkg_content = stdout_pkg.read().decode('utf-8', errors='replace').strip()
            if pkg_content and not pkg_content.startswith('Error') and not 'No such file' in pkg_content:
                try:
                    pkg_data = json.loads(pkg_content)
                    pkg_name = pkg_data.get('name', 'unknown')
                    dependencies = pkg_data.get('dependencies', {})
                    has_prisma = 'prisma' in dependencies or '@prisma/client' in dependencies
                    version = pkg_data.get('version', '')
                    print(f"\nContainer: {name} (ID: {cid})")
                    print(f"  Package Name: {pkg_name} (Version: {version})")
                    print(f"  Has Prisma: {has_prisma}")
                    print(f"  Next.js: {dependencies.get('next', 'no')}")
                    print(f"  React: {dependencies.get('react', 'no')}")
                except Exception as e:
                    # Not a valid JSON or failed to parse, maybe print first line
                    first_line = pkg_content.split('\n')[0]
                    print(f"\nContainer: {name} (ID: {cid}) - Failed to parse package.json: {e}")
                    print(f"  Content snippet: {first_line[:100]}")
                        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
