import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=10)
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/novesia-scraper/")
        print("=== /root/novesia-scraper/ ===")
        print(stdout.read().decode('utf-8'))
    except Exception as e:
        print("Error:", e)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
