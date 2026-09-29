import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)
cmd = 'docker exec supabase-db-og8gwooogk480gcws0o84ssc psql -U supabase_admin -d postgres -c "SELECT id, episode_number, video_url, is_active FROM episodes WHERE drama_id = \\'y8o6b5ff5tm1h1cq11wy81o7\\' ORDER BY episode_number;"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
