import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = "SELECT id, email, name, role, is_active FROM users WHERE role = 'admin' LIMIT 10;"
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== ADMIN USERS ===")
print(stdout.read().decode())

ssh.close()
