import psycopg2, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = c.cursor()
cur.execute("""SELECT id, title, description FROM "Drama" WHERE description LIKE '%%[FRkey:%%'""")
rows = cur.fetchall()
print(f'Total dramas with FRkey: {len(rows)}')
for r in rows:
    m = re.search(r'\[FRkey:([^\]]+)\]', r[2])
    frkey = m.group(1) if m else '?'
    print(f'{r[0][:12]} | {frkey:50s} | {r[1][:40]}')
c.close()
