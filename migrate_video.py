import sqlite3
import os

db_path = "indiawish.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE listings ADD COLUMN video_url TEXT")
        conn.commit()
        print("Successfully added video_url column to listings table.")
    except sqlite3.OperationalError as e:
        print(f"Error or already exists: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
