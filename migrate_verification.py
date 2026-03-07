import sqlite3

conn = sqlite3.connect('indiawish.db')
c = conn.cursor()

cols = [r[1] for r in c.execute('PRAGMA table_info(users)')]
print('existing cols:', cols)

if 'verification_level' not in cols:
    c.execute("ALTER TABLE users ADD COLUMN verification_level TEXT DEFAULT 'unverified'")
    print("Added verification_level")
else:
    print("verification_level already exists")

conn.commit()
conn.close()
print('Done')
