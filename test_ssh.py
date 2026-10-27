import paramiko
if not hasattr(paramiko, 'DSSKey'):
    try: paramiko.DSSKey = paramiko.dsskey.DSSKey
    except:
        class FakeDSSKey: pass
        paramiko.DSSKey = FakeDSSKey

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('141.11.160.187', port=22, username='root', password='Surya123!', timeout=15)
stdin, stdout, stderr = client.exec_command('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')
print(stdout.read().decode())
client.close()
