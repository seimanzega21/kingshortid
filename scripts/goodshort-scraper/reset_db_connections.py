"""Force kill all connections and reset"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to postgres database (not kingshort) to avoid connection locks
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/postgres')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

print("Terminating all connections to kingshort database...")

# Terminate all connections
cur.execute("""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'kingshort'
      AND pid <> pg_backend_pid()
""")

print(f"✅ Terminated {cur.rowcount} connections")

cur.close()
conn.close()

# Now test connection
conn2 = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
print("✅ Fresh connection established")
conn2.close()

print("\n🎉 Database reset complete! Ready for import.")
