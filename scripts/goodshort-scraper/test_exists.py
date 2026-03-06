import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Test the exact query from drama_exists()
book_ids = ['31001045572', '31001070612']

for book_id in book_ids:
    query = 'SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1'
    param = (f'%{book_id}%',)
    
    print(f"\nTesting BookID: {book_id}")
    print(f"Query: {query}")
    print(f"Param: {param}")
    
    cur.execute(query, param)
    result = cur.fetchone()
    
    if result:
        print(f"  ✓ FOUND: {result[0]}")
        
        # Get drama details
        cur.execute(f'SELECT title, LEFT(description, 100) FROM "Drama" WHERE id = \'{result[0]}\'')
        details = cur.fetchone()
        print(f"  Title: {details[0]}")
        print(f"  Description: {details[1]}...")
    else:
        print(f"  ✗ NOT FOUND")

conn.close()
