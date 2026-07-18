import mysql.connector

# DB Config
DB_HOST = "kingshort-mariadb-do-user-13763717-0.j.db.ondigitalocean.com"
DB_USER = "doadmin"
DB_PASS = "AVNS_i0pQj3Z6a6FvH0Y-U1E"
DB_NAME = "kingshort"
DB_PORT = 25060

def delete_drama(drama_id):
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )
    cursor = conn.cursor()
    
    # 1. Delete all episodes
    print(f"Deleting episodes for drama {drama_id}...")
    cursor.execute("DELETE FROM Episode WHERE dramaId = %s", (drama_id,))
    
    # 2. Delete drama
    print(f"Deleting drama {drama_id}...")
    cursor.execute("DELETE FROM Drama WHERE id = %s", (drama_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Deleted successfully!")

if __name__ == '__main__':
    delete_drama("v7j8h3x5evzvxxh5lnqcmv4r")
