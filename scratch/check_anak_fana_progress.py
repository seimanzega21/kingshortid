import boto3
from botocore.config import Config
import psycopg2
import paramiko
import sys

# Workaround for paramiko DSSKey error in newer versions
if not hasattr(paramiko, 'DSSKey'):
    try:
        paramiko.DSSKey = paramiko.dsskey.DSSKey
    except Exception:
        class FakeDSSKey:
            pass
        paramiko.DSSKey = FakeDSSKey

from sshtunnel import SSHTunnelForwarder

sys.stdout.reconfigure(encoding='utf-8')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_IP = '10.0.1.25'
DB_PORT = 5432
LOCAL_PORT = 5441

DB_USER = 'supabase_admin'
DB_PASS = 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64'
DB_NAME = 'postgres'

DRAMA_ID = 'cmlisfgr8006gtlqebrmv3cwm'
DRAMA_SLUG = 'melolo/anak-fana-penakluk-langit'

def check_progress():
    # 1. Check R2
    print("Checking R2 progress...")
    r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')
    
    prefix = f"{DRAMA_SLUG}/"
    res = r2.list_objects_v2(Bucket='shortlovers', Prefix=prefix)
    contents = res.get('Contents', [])
    
    v720_count = sum(1 for obj in contents if obj['Key'].endswith('.mp4') and '_540p' not in obj['Key'])
    v540_count = sum(1 for obj in contents if obj['Key'].endswith('_540p.mp4'))
    
    print(f"R2 Results:")
    print(f"  720p files: {v720_count}")
    print(f"  540p files: {v540_count}")
    
    # 2. Check DB
    print("\nChecking DB progress...")
    try:
        tunnel = SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASS,
            remote_bind_address=(DB_IP, DB_PORT),
            local_bind_address=('127.0.0.1', LOCAL_PORT),
            allow_agent=False,
            host_pkey_directories=[],
        )
        tunnel.start()
        
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=LOCAL_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*), COUNT(video_url_540p) 
            FROM episodes 
            WHERE drama_id = %s
        """, (DRAMA_ID,))
        total, count_540 = cur.fetchone()
        
        print(f"DB Results:")
        print(f"  Total episodes: {total}")
        print(f"  Episodes with video_url_540p: {count_540}")
        
        # Check last 5 updated or filled episodes
        cur.execute("""
            SELECT episode_number, video_url_540p 
            FROM episodes 
            WHERE drama_id = %s AND video_url_540p IS NOT NULL 
            ORDER BY episode_number DESC 
            LIMIT 5
        """, (DRAMA_ID,))
        last_updated = cur.fetchall()
        if last_updated:
            print("\nLatest updated episodes in DB:")
            for ep in last_updated:
                print(f"  Episode {ep[0]}: {ep[1]}")
                
        conn.close()
        tunnel.stop()
    except Exception as e:
        print(f"Failed to check DB: {e}")

if __name__ == '__main__':
    check_progress()
