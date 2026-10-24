import paramiko
import sys

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to VPS...")
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        sftp = ssh.open_sftp()

        print("Uploading updated files to VPS...")
        sftp.put(r'D:\kingshortid\admin\src\lib\r2-helper.ts', '/opt/kingshortid-api/admin/src/lib/r2-helper.ts')
        sftp.put(r'D:\kingshortid\admin\src\app\api\dramas\[id]\route.ts', '/opt/kingshortid-api/admin/src/app/api/dramas/[id]/route.ts')
        sftp.put(r'D:\kingshortid\cf-backend\src\routes\dramas.ts', '/opt/kingshortid-api/cf-backend/src/routes/dramas.ts')

        sftp.close()
        print("Files uploaded successfully.")

        # Rebuild admin container on VPS
        print("Rebuilding kingshort-admin container on VPS...")
        rebuild_cmd = """
cd /opt/kingshortid-api/admin && docker build -t kingshort-admin . && \
docker rm -f kingshort-admin-app && \
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
        stdin, stdout, stderr = ssh.exec_command(rebuild_cmd)
        exit_status = stdout.channel.recv_exit_status()
        print("Admin rebuild exit status:", exit_status)
        if exit_status == 0:
            print("Container ID:", stdout.read().decode().strip())
        else:
            print("Error:", stderr.read().decode())

        # Restart cf-backend on VPS
        print("Restarting cf-backend container...")
        stdin, stdout, stderr = ssh.exec_command("cd /opt/kingshortid-api/cf-backend && docker compose restart kingshortid-api")
        stdout.channel.recv_exit_status()
        print(stdout.read().decode())

        # Copy favicon to rebuilt container to ensure icon stays
        ssh.exec_command('docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/static/media/favicon.0b3bf435.ico 2>/dev/null; docker cp /opt/kingshortid-api/admin/public/favicon.png kingshort-admin-app:/app/.next/server/app/favicon.ico.body 2>/dev/null')

        ssh.close()
        print("Deployment complete.")
    except Exception as e:
        print("Error deploying to VPS:", e)

if __name__ == "__main__":
    main()
