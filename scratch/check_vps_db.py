import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

VPS_DB_URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres"

try:
    print("Connecting to VPS database...")
    conn = psycopg2.connect(VPS_DB_URL)
    cur = conn.cursor()
    print("Connection successful!")
    
    # Check if drama exists in dramas table
    cur.execute("SELECT id, title, code, is_active FROM dramas WHERE id = %s", ('cmlistfgr8006gtlqebrmv3cwm',))
    drama = cur.fetchone()
    if drama:
        print(f"DRAMA IN VPS DB:")
        print(f"  ID: {drama[0]}")
        print(f"  Title: {drama[1]}")
        print(f"  Code: {drama[2]}")
        print(f"  Is Active: {drama[3]}")
    else:
        print("Drama not found by ID in VPS DB. Searching by title...")
        cur.execute("SELECT id, title, code, is_active FROM dramas WHERE title ILIKE %s", ('%Anak Fana%',))
        drama = cur.fetchone()
        if drama:
            print(f"FOUND DRAMA BY TITLE SEARCH:")
            print(f"  ID: {drama[0]}")
            print(f"  Title: {drama[1]}")
            print(f"  Code: {drama[2]}")
            print(f"  Is Active: {drama[3]}")
        else:
            print("Drama not found by title either.")
            conn.close()
            sys.exit(0)
            
    drama_id = drama[0]
    
    # Query episodes
    cur.execute("""
        SELECT id, episode_number, title, video_url, video_url_540p, subtitle_url, is_active 
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
            print(f"  Video URL (Default/720p): {ep[3]}")
            print(f"  Video URL 540p: {ep[4]}")
            print(f"  Subtitle URL: {ep[5]}")
            print(f"  Is Active: {ep[6]}")
            
        # Analysis
        all_urls_720 = [ep[3] for ep in eps if ep[3]]
        all_urls_540 = [ep[4] for ep in eps if ep[4]]
        print(f"\nAnalysis:")
        print(f"  Total video_url: {len(all_urls_720)}")
        print(f"  Total video_url_540p: {len(all_urls_540)}")
        
        # Check extensions
        mp4_720 = sum(1 for u in all_urls_720 if u.lower().endswith('.mp4'))
        m3u8_720 = sum(1 for u in all_urls_720 if '.m3u8' in u.lower())
        print(f"  720p/default ending in .mp4: {mp4_720}")
        print(f"  720p/default contains .m3u8: {m3u8_720}")
        
        mp4_540 = sum(1 for u in all_urls_540 if u.lower().endswith('.mp4'))
        m3u8_540 = sum(1 for u in all_urls_540 if '.m3u8' in u.lower())
        print(f"  540p ending in .mp4: {mp4_540}")
        print(f"  540p contains .m3u8: {m3u8_540}")
        
    conn.close()
except Exception as e:
    print("Database connection error:", e)
