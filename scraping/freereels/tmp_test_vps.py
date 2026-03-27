import paramiko
paramiko.DSSKey = paramiko.RSAKey
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('141.11.160.187', username='root', password='Surya123!')

DB = 'supabase-db-og8gwooogk480gcws0o84ssc'

def run(sql):
    escaped = sql.replace("'", "'\\''")
    cmd = f"docker exec {DB} psql -U supabase_admin -d postgres -t -A -c '{escaped}'"
    stdin, stdout, stderr = c.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

print("=== dramas COLUMNS ===")
print(run("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='dramas' ORDER BY ordinal_position"))

print("\n=== episodes COLUMNS ===")
print(run("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='episodes' ORDER BY ordinal_position"))

print("\n=== COUNTS ===")
print(f"dramas: {run('SELECT count(*) FROM dramas')}")
print(f"episodes: {run('SELECT count(*) FROM episodes')}")

print("\n=== SAMPLE DRAMA ===")
print(run("SELECT id, title, total_episodes FROM dramas WHERE title ILIKE '%sulih%' LIMIT 5"))

c.close()
