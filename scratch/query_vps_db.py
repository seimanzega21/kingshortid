import paramiko

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
        
        # Run query inside the database container
        cmd = 'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "SELECT id, type, amount, description, reference, balance_after, created_at FROM coin_transactions WHERE user_id = \'p5ntsk0nv4a0c2aqyxjdwl7y\' ORDER BY created_at DESC LIMIT 15;"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("\n--- LATEST USERS ---")
        print(stdout.read().decode('utf-8'))
        print("Errors:")
        print(stderr.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
