import time
import sys
import os
import psycopg2
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

sys.stdout.reconfigure(encoding='utf-8')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_IP = '10.0.1.25'
DB_PORT = 5432
LOCAL_PORT = 5439  # Use a unique local port

print("Starting SSH tunnel...")
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
    print(f"SSH Tunnel active on local port {LOCAL_PORT} -> {DB_IP}:{DB_PORT}")
    
    # Connect using the tunnel
    # Try using postgres user and supabase_admin user
    users = ['supabase_admin', 'postgres']
    password = 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64'
    db_name = 'postgres'
    
    conn = None
    for user in users:
        try:
            print(f"Trying db connection with user '{user}'...")
            conn = psycopg2.connect(
                host='127.0.0.1',
                port=LOCAL_PORT,
                user=user,
                password=password,
                database=db_name
            )
            print(f"Successfully connected as '{user}'!")
            break
        except Exception as conn_err:
            print(f"Connection failed for '{user}': {conn_err}")
            
    if not conn:
        print("Could not connect to database through the tunnel.")
        tunnel.stop()
        sys.exit(1)
        
    cur = conn.cursor()
    
    # 1. Search for the drama in the database
    did = 'cmlisfgr8006gtlqebrmv3cwm'
    cur.execute("SELECT id, title, is_active FROM dramas WHERE id = %s", (did,))
    drama = cur.fetchone()
    if not drama:
        print("Drama not found by ID. Searching by title...")
        cur.execute("SELECT id, title, is_active FROM dramas WHERE title ILIKE %s", ('%Anak Fana%',))
        drama = cur.fetchone()
        
    if drama:
        print(f"\nDRAMA FOUND:")
        print(f"  ID: {drama[0]}")
        print(f"  Title: {drama[1]}")
        print(f"  Is Active: {drama[2]}")
        
        drama_id = drama[0]
        
        # 2. Query episodes
        cur.execute("""
            SELECT id, episode_number, title, video_url, video_url_540p, is_active 
            FROM episodes 
            WHERE drama_id = %s 
            ORDER BY episode_number ASC
        """, (drama_id,))
        eps = cur.fetchall()
        
        print(f"\nTotal episodes in database: {len(eps)}")
        if eps:
            print("\nFirst 3 episodes details:")
            for ep in eps[:3]:
                print(f"Episode {ep[1]}:")
                print(f"  ID: {ep[0]}")
                print(f"  Title: {ep[2]}")
                print(f"  Video URL (720p): {ep[3]}")
                print(f"  Video URL 540p  : {ep[4]}")
                print(f"  Is Active       : {ep[5]}")
                
            # Analysis
            all_urls_720 = [ep[3] for ep in eps if ep[3]]
            all_urls_540 = [ep[4] for ep in eps if ep[4]]
            print(f"\nAnalysis:")
            print(f"  Total video_url (720p): {len(all_urls_720)}")
            print(f"  Total video_url_540p  : {len(all_urls_540)}")
            
            # Check extensions
            mp4_720 = sum(1 for u in all_urls_720 if u.lower().endswith('.mp4'))
            m3u8_720 = sum(1 for u in all_urls_720 if '.m3u8' in u.lower())
            print(f"  720p/default ending in .mp4: {mp4_720}")
            print(f"  720p/default contains .m3u8: {m3u8_720}")
            
            mp4_540 = sum(1 for u in all_urls_540 if u.lower().endswith('.mp4'))
            m3u8_540 = sum(1 for u in all_urls_540 if '.m3u8' in u.lower())
            print(f"  540p ending in .mp4: {mp4_540}")
            print(f"  540p contains .m3u8: {m3u8_540}")
            
            # List some missing ones or details
            missing_540 = [ep[1] for ep in eps if not ep[4]]
            if missing_540:
                print(f"\nEpisodes missing 540p ({len(missing_540)} total):")
                print(f"  {missing_540[:10]}...")
            else:
                print("\nNo episodes missing 540p!")
                
    else:
        print("Drama 'Anak Fana Penakluk Langit' not found in remote DB.")
        
    conn.close()
    tunnel.stop()
    print("\nSSH Tunnel closed.")
    
except Exception as e:
    print("Error in script:", e)
