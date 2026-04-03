import psycopg2

DB_URL = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@10.0.3.14:5432/postgres'

def audit():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("=" * 60)
    print("  KINGSHORT VIDEO URL AUDIT")
    print("=" * 60)

    # Total episodes aktif
    cur.execute("SELECT COUNT(*) FROM episodes WHERE is_active = true")
    total = cur.fetchone()[0]
    print(f"\n📦 Total episode aktif: {total}")

    # Episode dengan URL dari R2 kita (stream.shortlovers.id atau r2.dev / r2.cloudflarestorage)
    cur.execute("""
        SELECT COUNT(*) FROM episodes
        WHERE is_active = true
        AND (
            video_url LIKE '%shortlovers.id%'
            OR video_url LIKE '%.r2.dev%'
            OR video_url LIKE '%.r2.cloudflarestorage.com%'
        )
    """)
    r2_count = cur.fetchone()[0]
    print(f"✅ Episode dari R2 kita: {r2_count}")

    # Episode dari server EXTERNAL (bukan R2 kita)
    cur.execute("""
        SELECT COUNT(*) FROM episodes
        WHERE is_active = true
        AND video_url NOT LIKE '%shortlovers.id%'
        AND video_url NOT LIKE '%.r2.dev%'
        AND video_url NOT LIKE '%.r2.cloudflarestorage.com%'
    """)
    ext_count = cur.fetchone()[0]
    print(f"⚠️  Episode dari server EXTERNAL: {ext_count}")

    # Detail drama yang masih punya external URL
    if ext_count > 0:
        print(f"\n--- Drama dengan episode external ---")
        cur.execute("""
            SELECT d.title, COUNT(e.id) as ext_eps,
                   SUBSTRING(MIN(e.video_url), 1, 80) as sample_url
            FROM episodes e
            JOIN dramas d ON d.id = e.drama_id
            WHERE e.is_active = true
            AND e.video_url NOT LIKE '%shortlovers.id%'
            AND e.video_url NOT LIKE '%.r2.dev%'
            AND e.video_url NOT LIKE '%.r2.cloudflarestorage.com%'
            GROUP BY d.title
            ORDER BY ext_eps DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        for title, cnt, sample in rows:
            print(f"  [{cnt} eps] {title}")
            print(f"           → {sample}")
    
    print("\n" + "=" * 60)
    print("  AUDIT 540p")
    print("=" * 60)

    # Episode yang PUNYA 540p
    cur.execute("""
        SELECT COUNT(*) FROM episodes
        WHERE is_active = true
        AND video_url_540p IS NOT NULL
        AND video_url_540p != ''
    """)
    has_540 = cur.fetchone()[0]
    print(f"\n✅ Episode dengan 540p: {has_540}")

    # Episode yang TIDAK punya 540p
    cur.execute("""
        SELECT COUNT(*) FROM episodes
        WHERE is_active = true
        AND (video_url_540p IS NULL OR video_url_540p = '')
    """)
    no_540 = cur.fetchone()[0]
    print(f"❌ Episode TANPA 540p: {no_540}")

    # Drama yang punya setidaknya satu episode dengan 540p
    cur.execute("""
        SELECT COUNT(DISTINCT drama_id) FROM episodes
        WHERE is_active = true
        AND video_url_540p IS NOT NULL AND video_url_540p != ''
    """)
    dramas_with_540 = cur.fetchone()[0]
    print(f"\n🎬 Drama yang sudah punya 540p: {dramas_with_540}")

    # Drama yang BELUM punya 540p sama sekali
    cur.execute("""
        SELECT d.title, COUNT(e.id) as ep_count
        FROM dramas d
        JOIN episodes e ON e.drama_id = d.id
        WHERE e.is_active = true
        AND d.id NOT IN (
            SELECT DISTINCT drama_id FROM episodes
            WHERE is_active = true
            AND video_url_540p IS NOT NULL AND video_url_540p != ''
        )
        GROUP BY d.title
        ORDER BY ep_count DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    if rows:
        print(f"\n--- Drama yang belum ada 540p sama sekali ---")
        for title, cnt in rows:
            print(f"  [{cnt} eps] {title}")

    print("\n" + "=" * 60)
    cur.close()
    conn.close()

if __name__ == '__main__':
    audit()
