import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

titles = [
    'Setelah Bertapa, Kutaklukkan Dunia',
    'Siapa yang Sedang Membicarakan Kaisar',
    'Sistem Perubah Nasib',
    'Sistem Suami Sultan',
    'Tahun 1977 Penuh Peluang',
]

for t in titles:
    cur.execute('SELECT id, cover FROM "Drama" WHERE title = %s', (t,))
    row = cur.fetchone()
    if row:
        print(f"{t}")
        print(f"  cover: {row[1]}")
    else:
        print(f"{t} - NOT FOUND")

cur.close()
conn.close()
