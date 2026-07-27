import paramiko
import sys

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Connecting to VPS (141.11.160.187)...")
        ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
        
        print("\n=== SYSTEM HEALTH ===")
        stdin, stdout, stderr = ssh.exec_command('uptime && free -h && df -h /')
        print(stdout.read().decode())
        
        print("\n=== RUNNING SCRAPING PROCESSES ===")
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[i]ngest_"')
        out = stdout.read().decode().strip()
        if out:
            print(out)
        else:
            print("No ingest processes running.")
            
        print("\n=== LATEST DRAMAWAVEV2 LOGS ===")
        stdin, stdout, stderr = ssh.exec_command('tail -n 20 /var/log/ingest_nikah_habis_turun_gunung.log')
        print(stdout.read().decode())
        
    except Exception as e:
        print("SSH Connection failed:", e)
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
