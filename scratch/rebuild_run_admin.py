import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)

stdin, stdout, stderr = ssh.exec_command('docker build -t kingshort-admin /opt/kingshortid-api/admin')
print("Building image...")
for line in stdout:
    print(line.strip())

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
run_cmd = f"docker run -d --name kingshort-admin-app --network og8gwooogk480gcws0o84ssc --restart always {env_args} kingshort-admin"

print("\nRunning container without host port binding...")
stdin, stdout, stderr = ssh.exec_command(run_cmd)
print("Container ID:", stdout.read().decode().strip())
print("Error:", stderr.read().decode().strip())

ssh.close()
