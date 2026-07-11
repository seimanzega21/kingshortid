import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

def query(q):
    _, stdout, _ = ssh.exec_command(f'docker exec supabase-db-og8gwooogk480gcws0o84ssc psql -U supabase_admin -d postgres -t -c "{q}"')
    return stdout.read().decode().strip()

print('Users:', query("SELECT COUNT(*) FROM users;"))
print('Dramas:', query("SELECT COUNT(*) FROM dramas;"))
print('Views:', query("SELECT SUM(views) FROM dramas;"))
print('Watch History:', query("SELECT COUNT(*) FROM watch_history;"))
print('Coin Transactions:', query("SELECT SUM(amount) FROM coin_transactions WHERE type='topup';"))

ssh.close()
