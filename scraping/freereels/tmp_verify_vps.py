import paramiko
paramiko.DSSKey = paramiko.RSAKey
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('141.11.160.187', username='root', password='Surya123!')

DB = 'supabase-db-og8gwooogk480gcws0o84ssc'

def run(sql):
    escaped = sql.replace("'", "'\\''")
    cmd = f"docker exec {DB} psql -U supabase_admin -d postgres -t -A -c '{escaped}'"
    stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Counts
print(f"Total dramas: {run('SELECT count(*) FROM dramas')}")
print(f"Total episodes: {run('SELECT count(*) FROM episodes')}")

# FreeReels-specific
print(f"\nFreeReels (Sulih Suara) dramas:")
result = run("""SELECT title, is_active, total_episodes,
    (SELECT COUNT(*) FROM episodes e WHERE e.drama_id = d.id) as actual_eps,
    (SELECT COUNT(*) FROM episodes e WHERE e.drama_id = d.id AND e.video_url LIKE '%stream.shortlovers%') as r2_eps
    FROM dramas d 
    WHERE title ILIKE '%Sulih%' OR tag_list::text ILIKE '%Dubbing%'
    ORDER BY title""")

for line in result.split('\n'):
    if line.strip():
        parts = line.split('|')
        if len(parts) >= 5:
            t, active, total, actual, r2 = parts[:5]
            status = 'PUB' if active.strip() == 't' else 'PEND'
            print(f"  [{status}] {t.strip()[:42]:42s} | {actual.strip():>3s}/{total.strip():>3s} eps | R2:{r2.strip()}")

# Count pending/published
pending = run("SELECT count(*) FROM dramas WHERE is_active = false AND (title ILIKE '%Sulih%' OR tag_list::text ILIKE '%Dubbing%')")
published = run("SELECT count(*) FROM dramas WHERE is_active = true AND (title ILIKE '%Sulih%' OR tag_list::text ILIKE '%Dubbing%')")
print(f"\nSummary: {pending} pending, {published} published")

c.close()
