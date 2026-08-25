import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print('Restarting supabase API containers...')
    ssh.exec_command('docker restart $(docker ps -q -f name=supabase-rest)')
    ssh.exec_command('docker restart $(docker ps -q -f name=supabase-kong)')
    ssh.exec_command('docker restart $(docker ps -q -f name=supabase-db)')
    print('Restarted API containers.')
except Exception as e:
    print('Failed:', e)
finally:
    ssh.close()
