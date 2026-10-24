import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
SELECT cover, count(*) as count, array_agg(title) as titles
FROM dramas
WHERE cover LIKE '%stream.shortlovers.id%'
GROUP BY cover
HAVING count(*) > 1
LIMIT 20;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== SHARED COVERS IN DB ===")
print(stdout.read().decode())

ssh.close()
