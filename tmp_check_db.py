import sqlite3
conn = sqlite3.connect('indiawish.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([r[0] for r in cur.fetchall()])

cur.execute("SELECT * FROM categories")
rows = cur.fetchall()
print(f"Categories count: {len(rows)}")
for r in rows:
    print(r)

try:
    cur.execute("SELECT * FROM subcategories")
    rows = cur.fetchall()
    print(f"Subcategories count: {len(rows)}")
except Exception as e:
    print(f"Subcategories table error: {e}")

conn.close()
