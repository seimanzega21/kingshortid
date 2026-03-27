"""
Fix VPS: Set all FreeReels episodes to is_active = true
=========================================================
The admin panel proxies all /api/dramas/* to VPS API (api.shortlovers.id).
VPS API uses Drizzle schema where episodes have is_active=false.
This script updates episodes to is_active=true.
"""
import paramiko
paramiko.DSSKey = paramiko.RSAKey
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_CONTAINER = 'supabase-db-og8gwooogk480gcws0o84ssc'

def run(c, sql):
    escaped = sql.replace("'", "'\\''")
    cmd = f"docker exec {DB_CONTAINER} psql -U supabase_admin -d postgres -t -A -c '{escaped}'"
    stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if err and 'ERROR' in err:
        print(f"  SQL ERROR: {err}")
    return out

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS)

print("=" * 60)
print("  VPS: Fix FreeReels Episode Visibility")
print("=" * 60)

# Check current state
result = run(c, "SELECT count(*), sum(CASE WHEN is_active THEN 1 ELSE 0 END) as active, sum(CASE WHEN NOT is_active THEN 1 ELSE 0 END) as inactive FROM episodes")
parts = result.split('|')
print(f"\n  Current VPS episodes:")
print(f"    Total: {parts[0] if parts else '?'}")
print(f"    Active: {parts[1] if len(parts) > 1 else '?'}")
print(f"    Inactive: {parts[2] if len(parts) > 2 else '?'}")

# Check FreeReels dramas specifically
result2 = run(c, """
    SELECT d.title, count(e.id) as total_eps, 
           sum(CASE WHEN e.is_active THEN 1 ELSE 0 END) as active_eps,
           sum(CASE WHEN NOT e.is_active THEN 1 ELSE 0 END) as inactive_eps
    FROM dramas d 
    JOIN episodes e ON e.drama_id = d.id
    WHERE d.is_active = false
    GROUP BY d.title
    ORDER BY d.title
""")

print(f"\n  Pending dramas with episodes:")
for line in result2.split('\n'):
    if '|' in line:
        parts = line.split('|')
        name = parts[0][:35]
        tot = parts[1].strip()
        act = parts[2].strip()
        inact = parts[3].strip()
        print(f"    {name:35s} | {tot:3s} eps (act:{act}, inact:{inact})")

# UPDATE: Set all episodes of pending dramas to is_active = true
print(f"\n  Updating episodes to is_active = true...")
result3 = run(c, """
    UPDATE episodes 
    SET is_active = true 
    WHERE is_active = false 
    AND drama_id IN (SELECT id FROM dramas WHERE is_active = false)
""")
print(f"  Updated: {result3}")

# Also check the VPS API response for a specific drama
# Let's test the VPS drama detail endpoint directly
result4 = run(c, """
    SELECT d.title, 
           (SELECT count(*) FROM episodes WHERE drama_id = d.id AND is_active = true) as visible_eps
    FROM dramas d 
    WHERE d.title ILIKE '%Bos Kuliah%'
""")
print(f"\n  After fix — Bos Kuliah visible episodes:")
print(f"    {result4}")

c.close()

print(f"\n{'=' * 60}")
print(f"  ✅ Episodes set to is_active=true")
print(f"  → Dramas still pending (is_active=false) in admin panel")
print(f"  → Episodes should now appear in admin drama detail")
print(f"{'=' * 60}")
