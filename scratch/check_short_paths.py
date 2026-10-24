import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
SELECT video_url
FROM episodes
WHERE video_url LIKE '%stream.shortlovers.id%'
  AND array_length(string_to_array(regexp_replace(video_url, '^https?://[^/]+/', ''), '/'), 1) <= 2
LIMIT 20;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== SHORT PATHS (< 3 segments) ===")
print(stdout.read().decode())

ssh.close()
