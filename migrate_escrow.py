import sqlite3
import os

db_path = "indiawish.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escrows (
                id TEXT PRIMARY KEY,
                listing_id TEXT NOT NULL,
                buyer_id TEXT NOT NULL,
                seller_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'held',
                upi_ref TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(listing_id) REFERENCES listings(id),
                FOREIGN KEY(buyer_id) REFERENCES users(id),
                FOREIGN KEY(seller_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("Successfully created escrows table.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
