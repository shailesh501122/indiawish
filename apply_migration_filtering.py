import sqlite3
import os

def migrate():
    db_path = 'indiawish.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding 'properties' to 'listings'...")
        # Check if column exists first
        cursor.execute("PRAGMA table_info(listings)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'properties' not in columns:
            cursor.execute("ALTER TABLE listings ADD COLUMN properties JSON DEFAULT '{}'")
            print("Added 'properties' to 'listings'")
        else:
            print("'properties' already exists in 'listings'")
    except sqlite3.OperationalError as e:
        print(f"Listings Error: {e}")

    try:
        print("Adding 'filter_config' to 'categories'...")
        cursor.execute("PRAGMA table_info(categories)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'filter_config' not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN filter_config JSON DEFAULT '[]'")
            print("Added 'filter_config' to 'categories'")
        else:
            print("'filter_config' already exists in 'categories'")
    except sqlite3.OperationalError as e:
        print(f"Categories Error: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
