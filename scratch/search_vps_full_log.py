import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=10)
        
        # Check scraper.log
        cmd1 = "grep -in 'Mendengar' /opt/microdrama/scraper.log"
        stdin, stdout, stderr = ssh.exec_command(cmd1)
        print("=== Matches in scraper.log ===")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        # Check microdrama_mp4_v5.log
        cmd2 = "grep -in 'Mendengar' /opt/microdrama/microdrama_mp4_v5.log"
        stdin, stdout, stderr = ssh.exec_command(cmd2)
        print("=== Matches in microdrama_mp4_v5.log ===")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
    except Exception as e:
        print("Error:", e)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
