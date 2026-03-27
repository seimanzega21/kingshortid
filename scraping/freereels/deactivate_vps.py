"""Set all Dubbing dramas to inactive on VPS"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:15432/postgres'
conn = psycopg2.connect(VPS)
cur = conn.cursor()

cur.execute("""UPDATE dramas SET is_active = false WHERE tag_list::text LIKE '%Dubbing%'""")
print(f'Deactivated {cur.rowcount} Dubbing dramas')

cur.execute("""UPDATE episodes SET is_active = false WHERE drama_id IN 
               (SELECT id FROM dramas WHERE tag_list::text LIKE '%Dubbing%')""")
print(f'Deactivated {cur.rowcount} episodes')

conn.commit()
conn.close()
print('Done! Dramas tidak akan muncul di mobile app.')
