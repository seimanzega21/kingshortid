import psycopg2
conn = psycopg2.connect('postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres')
cur = conn.cursor()
cur.execute("UPDATE dramas SET is_featured = false;")
cur.execute("INSERT INTO app_settings (key, value, updated_at) VALUES ('bannerMode', 'auto', extract(epoch from now())), ('bannerRotationDays', '1', extract(epoch from now())) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at;")
conn.commit()
conn.close()
print('Done')
