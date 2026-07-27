import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('141.11.160.187', username='root', password='Surya123!', timeout=15)
    print("=== LAPORAN PROGRESS DARI DATABASE ===")
    
    cmd = '''
    docker exec $(docker ps -qf "name=mysql" -f "name=mariadb" -f "name=db") mysql -u root -p'password' kingshort -e "
    SELECT d.title, COUNT(e.id) as uploaded_episodes 
    FROM Drama d 
    LEFT JOIN Episode e ON d.id = e.dramaId 
    WHERE d.title IN ('Gebetan Rahasia Suamiku', 'Raja Keberuntungan Berkekuatan Super', 'Kembalinya Legenda Istana', 'Bos Mafia Hasrat Terlarangku') 
    GROUP BY d.id;
    "
    '''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    if out:
        print(out)
    else:
        print("Belum ada data masuk atau gagal query database.")
except Exception as e:
    print("Gagal connect SSH:", e)
finally:
    ssh.close()
