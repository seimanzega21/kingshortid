import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
SELECT d.id, d.title, d.cover,
       (SELECT e.video_url FROM episodes e WHERE e.drama_id = d.id AND e.video_url IS NOT NULL LIMIT 1) as sample_video
FROM dramas d
WHERE d.cover LIKE '%stream.shortlovers.id%' OR d.id IN (
    SELECT drama_id FROM episodes WHERE video_url LIKE '%stream.shortlovers.id%' LIMIT 10
)
LIMIT 15;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print("STDERR:", stderr.read().decode())

ssh.close()
