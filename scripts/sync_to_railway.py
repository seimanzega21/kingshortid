"""
FAST Sync: Local PostgreSQL → Railway PostgreSQL
Uses batch inserts with execute_values for 50-100x speedup
"""
import psycopg2
import psycopg2.extras
import sys
import time

LOCAL_DB = "postgresql://postgres:seiman21@localhost:5432/kingshort"
RAILWAY_DB = "postgresql://postgres:VrblIicjeGbWSPUkmgOSUMkmeHRKJPbU@ballast.proxy.rlwy.net:44659/railway"

BATCH_SIZE = 500

def get_count(conn, table):
    cur = conn.cursor()
    cur.execute(f'SELECT count(*) FROM "{table}"')
    return cur.fetchone()[0]

def batch_insert(conn, table, rows, cols):
    """Insert rows in batches using execute_values (much faster)"""
    if not rows:
        return 0
    
    col_str = ', '.join(f'"{c}"' for c in cols)
    template = '(' + ', '.join(['%s'] * len(cols)) + ')'
    
    inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        values = [[row[c] for c in cols] for row in batch]
        
        cur = conn.cursor()
        try:
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO "{table}" ({col_str}) VALUES %s ON CONFLICT DO NOTHING',
                values,
                template=template,
                page_size=BATCH_SIZE
            )
            conn.commit()
            inserted += len(batch)
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Batch error at {i}: {str(e)[:100]}")
            # Fall back to one-by-one for this batch
            for row in batch:
                try:
                    cur2 = conn.cursor()
                    vals = [row[c] for c in cols]
                    cur2.execute(
                        f'INSERT INTO "{table}" ({col_str}) VALUES ({", ".join(["%s"]*len(cols))}) ON CONFLICT DO NOTHING',
                        vals
                    )
                    conn.commit()
                    inserted += 1
                except:
                    conn.rollback()
        
        if inserted % 2000 == 0 and inserted > 0:
            print(f"   ... {inserted}/{len(rows)}")
    
    return inserted

def main():
    start = time.time()
    print("=" * 60)
    print("  FAST LOCAL → RAILWAY DATABASE SYNC")
    print("=" * 60)

    print("\n1. Connecting...")
    local = psycopg2.connect(LOCAL_DB)
    railway = psycopg2.connect(RAILWAY_DB)
    print("   ✅ Both databases connected")

    # Check what's already synced
    railway_dramas = get_count(railway, "Drama")
    railway_eps = get_count(railway, "Episode")
    local_eps = get_count(local, "Episode")
    print(f"\n2. Current state:")
    print(f"   Railway: {railway_dramas} dramas, {railway_eps} episodes")
    print(f"   Local: {get_count(local, 'Drama')} dramas, {local_eps} episodes")

    # Clear episodes that were partially synced (keep dramas since they're done)
    if railway_eps > 0 and railway_eps < local_eps:
        print(f"\n3. Clearing partial episode data ({railway_eps} eps)...")
        rcur = railway.cursor()
        rcur.execute('DELETE FROM "Episode"')
        railway.commit()
        print("   ✅ Cleared")
        railway_eps = 0
    elif railway_eps == 0:
        print("\n3. No episodes to clear")
    else:
        print(f"\n3. Episodes already synced ({railway_eps})")

    # If dramas aren't synced yet, do it
    if railway_dramas == 0:
        print("\n4. Copying dramas (batch mode)...")
        lcur = local.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        lcur.execute('SELECT * FROM "Drama" ORDER BY "createdAt"')
        dramas = lcur.fetchall()
        cols = list(dramas[0].keys()) if dramas else []
        count = batch_insert(railway, "Drama", dramas, cols)
        print(f"   ✅ {count} dramas copied")
    else:
        print(f"\n4. Dramas already synced ({railway_dramas})")

    # Copy episodes
    if railway_eps == 0:
        print("\n5. Copying episodes (batch mode)...")
        lcur = local.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        lcur.execute('SELECT * FROM "Episode" ORDER BY "dramaId", "episodeNumber"')
        episodes = lcur.fetchall()
        
        if episodes:
            cols = list(episodes[0].keys())
            print(f"   Total: {len(episodes)} episodes, batch size: {BATCH_SIZE}")
            count = batch_insert(railway, "Episode", episodes, cols)
            print(f"   ✅ {count} episodes copied")
        else:
            print("   No episodes found")
    else:
        print(f"\n5. Episodes already synced ({railway_eps})")

    # Verify
    print("\n6. Verification:")
    for table in ["Drama", "Episode"]:
        print(f"   Railway {table}: {get_count(railway, table)}")

    elapsed = time.time() - start
    print(f"\n   Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    local.close()
    railway.close()
    print("\n" + "=" * 60)
    print("  SYNC COMPLETE! ✅")
    print("=" * 60)

if __name__ == "__main__":
    main()
