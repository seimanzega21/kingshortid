import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

# 1. Update /opt/kingshortid-api/cf-backend/docker-compose.yml to remove "3000:3000"
stdin, stdout, stderr = ssh.exec_command('sed -i "/ports:/,/3000:3000/d" /opt/kingshortid-api/cf-backend/docker-compose.yml')
stdout.channel.recv_exit_status()

# 2. Re-create kingshortid-api without host port binding
cmd = "cd /opt/kingshortid-api/cf-backend && docker compose up -d kingshortid-api"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Compose output:")
print(stdout.read().decode())
print(stderr.read().decode())

# 3. Update deploy_admin.py and re-run kingshort-admin-app without -p 3002:3000
stdin, stdout, stderr = ssh.exec_command('sed -i "s/-p 3002:3000 //g" /opt/kingshortid-api/deploy_admin.py /root/kingshort-admin/deploy_admin.py 2>/dev/null')
stdout.channel.recv_exit_status()

# Recreate kingshort-admin-app without -p 3002:3000
ENV_VARS = {
    "DATABASE_URL": "postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@supabase-db-og8gwooogk480gcws0o84ssc:5432/postgres",
    "JWT_SECRET": "MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13",
    "ADMIN_API_KEY": "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14",
    "BACKEND_URL": "http://kingshortid-api:3000/api",
    "R2_ENDPOINT": "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com",
    "R2_ACCESS_KEY_ID": "07c99c897986ea52703c1285308d5e2c",
    "R2_SECRET_ACCESS_KEY": "44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44",
    "R2_BUCKET_NAME": "shortlovers",
    "R2_PUBLIC_URL": "https://stream.shortlovers.id",
    "NODE_ENV": "production",
    "NEXT_TELEMETRY_DISABLED": "1"
}
env_args = " ".join([f'-e {k}="{v}"' for k, v in ENV_VARS.items()])
recreate_admin = (
    "docker rm -f kingshort-admin-app && "
    f"docker run -d --name kingshort-admin-app --network og8gwooogk480gcws0o84ssc --restart always {env_args} kingshort-admin"
)
stdin, stdout, stderr = ssh.exec_command(recreate_admin)
print("Admin recreation output:")
print(stdout.read().decode())
print(stderr.read().decode())

# 4. Remove UFW rule for port 3002
stdin, stdout, stderr = ssh.exec_command('ufw delete allow 3002 2>/dev/null; ufw delete allow 3002/tcp 2>/dev/null; ufw reload')
stdout.channel.recv_exit_status()

# 5. Check ports now
stdin, stdout, stderr = ssh.exec_command('docker ps --filter "name=kingshort" --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"')
print("\n=== KSHORT CONTAINERS PORTS ===")
print(stdout.read().decode())

ssh.close()
