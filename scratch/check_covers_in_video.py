import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
SELECT id, drama_id, video_url
FROM episodes
WHERE video_url LIKE '%/dramas/covers/%'
LIMIT 20;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== EPISODES IN /dramas/covers/ ===")
print(stdout.read().decode())

ssh.close()
