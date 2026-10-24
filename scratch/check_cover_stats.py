import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
SELECT count(*) as total_dramas,
       count(CASE WHEN cover IS NULL OR cover = '' THEN 1 END) as empty_covers,
       count(CASE WHEN cover LIKE '%stream.shortlovers.id%' THEN 1 END) as r2_covers,
       count(CASE WHEN cover NOT LIKE '%stream.shortlovers.id%' AND cover IS NOT NULL AND cover != '' THEN 1 END) as external_covers
FROM dramas;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== COVER STATS IN DB ===")
print(stdout.read().decode())

ssh.close()
