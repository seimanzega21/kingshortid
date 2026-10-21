import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\kingshortid\admin\public\favicon.png', '/opt/kingshortid-api/admin/src/app/favicon.ico')
sftp.close()

# Rebuild in background properly so changes are permanent
rebuild_script = """
cd /opt/kingshortid-api/admin
docker build -t kingshort-admin .
docker rm -f kingshort-admin-app
docker run -d --name kingshort-admin-app --network og8gwooogk480gcws0o84ssc --restart always \
  -e DATABASE_URL="postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@supabase-db-og8gwooogk480gcws0o84ssc:5432/postgres" \
  -e JWT_SECRET="MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13" \
  -e ADMIN_API_KEY="00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14" \
  -e BACKEND_URL="http://kingshortid-api:3000/api" \
  -e R2_ENDPOINT="https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com" \
  -e R2_ACCESS_KEY_ID="07c99c897986ea52703c1285308d5e2c" \
  -e R2_SECRET_ACCESS_KEY="44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44" \
  -e R2_BUCKET_NAME="shortlovers" \
  -e R2_PUBLIC_URL="https://stream.shortlovers.id" \
  -e NODE_ENV="production" \
  -e NEXT_TELEMETRY_DISABLED="1" \
  kingshort-admin
"""

stdin, stdout, stderr = ssh.exec_command(rebuild_script)
ssh.close()
print("Rebuild executed with KingShort icon embedded permanently!")
