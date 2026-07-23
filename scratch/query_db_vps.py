import paramiko, sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=30)
except Exception as e:
    print('Connect error:', e)
    sys.exit(1)

cmd = '''
docker exec $(docker ps -qf "name=mysql" -f "name=mariadb" -f "name=db") mysql -u root -p'password' -e "
USE kingshort;
SELECT id, title, totalEpisodes, isActive FROM Drama WHERE title LIKE '%Kasih Tunggal%';
"
'''

stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:')
print(stdout.read().decode())
print('STDERR:')
print(stderr.read().decode())
ssh.close()
