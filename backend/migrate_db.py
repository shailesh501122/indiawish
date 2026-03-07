import sqlite3

def migrate():
    conn = sqlite3.connect('indiawish.db')
    cursor = conn.cursor()

    try:
        # Add images column to listings
        cursor.execute("ALTER TABLE listings ADD COLUMN images JSON DEFAULT '[]'")
        print("Added images column to listings")
    except sqlite3.OperationalError:
        print("images column already exists in listings or table missing")

    try:
        # Add images column to properties
        cursor.execute("ALTER TABLE properties ADD COLUMN images JSON DEFAULT '[]'")
        print("Added images column to properties")
    except sqlite3.OperationalError:
        print("images column already exists in properties or table missing")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
