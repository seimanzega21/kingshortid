import paramiko

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
    
    cmd = 'curl -X DELETE http://localhost:3000/api/admin/dramas/v7j8h3x5evzvxxh5lnqcmv4r -H "x-admin-key: 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("Delete response:", stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print("Error:", e)
