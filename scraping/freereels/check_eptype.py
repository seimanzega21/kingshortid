"""Check Episode.id column type and last inserted episodes"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Column types
cur.execute("""SELECT column_name, data_type, column_default, is_nullable 
               FROM information_schema.columns 
               WHERE table_name = 'Episode' 
               ORDER BY ordinal_position""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} (default={r[2]}, nullable={r[3]})')

# Last inserted episodes
print('\nLast episodes for Bos Kuliah Lagi:')
cur.execute("""SELECT id, "episodeNumber", "videoUrl", duration 
               FROM "Episode" WHERE "dramaId" = 'ff7862e6-23fb-4ed2-9407-6355af6e2f71' 
               ORDER BY "episodeNumber" """)
for r in cur.fetchall():
    print(f'  Ep {r[1]}: id={r[0]}, dur={r[3]}, url={r[2][:60]}')
conn.close()
