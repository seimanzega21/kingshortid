import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').split('?')[0])
cur = conn.cursor()

desc = 'Seorang anak yang dibuang oleh keluarganya kini bangkit kembali. Dengan tekad kuat, ia membuktikan bahwa takdir bisa diubah melalui kerja keras dan keberanian. Kisah kelahiran kembali penuh aksi serangan balik yang menggetarkan!'

cur.execute('UPDATE "Drama" SET description = %s WHERE title = %s AND "isActive" = true', (desc, 'Hidup Berjaya Anak Terbuang'))
conn.commit()

# Verify all
cur.execute("""SELECT title, LEFT(description, 80) FROM "Drama" WHERE "isActive" = true AND (description LIKE 'Drama pendek:%' OR description IS NULL OR LENGTH(description) < 20)""")
remaining = cur.fetchall()
print(f"Remaining bad descriptions: {len(remaining)}")
for r in remaining:
    print(f"  {r[0]}: {r[1]}")

if not remaining:
    print("All descriptions are now good! ✅")

cur.close()
conn.close()
