import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

query = """
WITH ep_prefixes AS (
    SELECT DISTINCT
        drama_id,
        regexp_replace(video_url, '^https?://[^/]+/(.*)/[^/]+$', '\\1') as prefix
    FROM episodes
    WHERE video_url LIKE '%stream.shortlovers.id%'
)
SELECT prefix, count(DISTINCT drama_id) as drama_count, array_agg(DISTINCT drama_id) as drama_ids
FROM ep_prefixes
GROUP BY prefix
HAVING count(DISTINCT drama_id) > 1
ORDER BY drama_count DESC;
"""
cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== SHARED PREFIXES BETWEEN DIFFERENT DRAMAS ===")
print(stdout.read().decode())

ssh.close()
