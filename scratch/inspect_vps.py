import paramiko

import sys

def inspect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("141.11.160.187", username="root", password="Surya123!", timeout=10)
        
        def run(cmd, label):
            print(f"\n{'='*20} {label} {'='*20}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore').strip()
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            enc = sys.stdout.encoding or 'utf-8'
            if out:
                print(out.encode(enc, errors='replace').decode(enc))
            if err:
                print("ERR:", err.encode(enc, errors='replace').decode(enc))

        run("date", "VPS Local Time")
        run("ps aux | grep -i python", "Python Processes")
        run("pm2 jlist | python3 -c \"import sys, json; data = json.load(sys.stdin); [print(x['name'], '->', x['pm2_env'].get('pm_exec_path'), '| status:', x['pm2_env'].get('status')) for x in data]\"", "PM2 Apps Exec Paths")
        run("systemctl list-units --type=service | grep -i -E 'scrape|drama|micro'", "Systemd Services")
        run("ls -la /opt/microdrama", "Microdrama Folder Files")
        run("tail -n 100 /opt/microdrama/scraper.log", "Last 100 lines of scraper.log")
        run("crontab -l", "Cron Jobs")
        
    except Exception as e:
        print("Error connecting to VPS:", e)
    finally:
        ssh.close()

if __name__ == "__main__":
    inspect()
