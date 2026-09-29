import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=10)
cmd = 'docker exec supabase-db-og8gwooogk480gcws0o84ssc psql -U supabase_admin -d postgres -c "UPDATE episodes SET video_url = NULL WHERE video_url = \'\' OR video_url = \' \' OR video_url LIKE \'https://stream.shortlovers.id/dramas/netshort/kebangkitan-kera-sakti%\';"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
