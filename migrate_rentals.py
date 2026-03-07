import sqlite3

conn = sqlite3.connect('indiawish.db')
c = conn.cursor()

cols = [r[1] for r in c.execute('PRAGMA table_info(listings)')]
print('existing listings cols:', cols)

if 'listing_type' not in cols:
    c.execute("ALTER TABLE listings ADD COLUMN listing_type TEXT DEFAULT 'sell'")
    print("Added listing_type")
if 'rent_price' not in cols:
    c.execute("ALTER TABLE listings ADD COLUMN rent_price REAL")
    print("Added rent_price")
if 'rent_period' not in cols:
    c.execute("ALTER TABLE listings ADD COLUMN rent_period TEXT")
    print("Added rent_period")

conn.commit()
conn.close()
print('Rental migration complete')
