import psycopg2
conn=psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur=conn.cursor()
cur.execute('ALTER TABLE "Episode" ADD COLUMN IF NOT EXISTS "videoUrl540p" TEXT;')
conn.commit()
cur.close()
conn.close()
print("Column added successfully!")
