import time
import sys
import paramiko
# Workaround for paramiko DSSKey error in newer versions
if not hasattr(paramiko, 'DSSKey'):
    try:
        paramiko.DSSKey = paramiko.dsskey.DSSKey
    except Exception:
        class FakeDSSKey:
            pass
        paramiko.DSSKey = FakeDSSKey

from sshtunnel import SSHTunnelForwarder

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_IP = '127.0.0.1'
DB_PORT = 5432
LOCAL_PORT = 5435

def start_tunnel():
    print(f"Establishing SSH tunnel to {SSH_HOST}...")
    try:
        server = SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASS,
            remote_bind_address=(DB_IP, DB_PORT),
            local_bind_address=('127.0.0.1', LOCAL_PORT),
            allow_agent=False,
            host_pkey_directories=[],
        )
        server.start()
        print(f"SSH Tunnel successfully started! Local port {LOCAL_PORT} is forwarded to {DB_IP}:{DB_PORT}.")
        print("Keep this process running to maintain database connection.")
        
        while True:
            # Check if tunnel is active
            if not server.is_active:
                print("Tunnel lost connection. Attempting to restart...")
                server.restart()
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nShutting down SSH tunnel...")
        server.stop()
        print("Tunnel closed.")
    except Exception as e:
        print("Error in SSH tunnel:", e)

if __name__ == "__main__":
    start_tunnel()
