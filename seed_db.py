import sqlite3
import uuid
import json
from datetime import datetime

def seed():
    conn = sqlite3.connect('indiawish.db')
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM listings")
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM users")

    # Add a user
    user_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users (id, first_name, last_name, email, hashed_password, phone_number, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, "John", "Doe", "john@example.com", "hashed_pw", "9876543210", 1))

    # Add categories
    cat_ids = [str(uuid.uuid4()) for _ in range(5)]
    categories = [
        (cat_ids[0], "Electronics", "Gadgets and more", "phone_android"),
        (cat_ids[1], "Real Estate", "Homes and lands", "home"),
        (cat_ids[2], "Vehicles", "Cars and bikes", "directions_car"),
        (cat_ids[3], "Fashion", "Clothing and accessories", "checkroom"),
        (cat_ids[4], "Furniture", "Home decor", "chair"),
    ]
    cursor.executemany("INSERT INTO categories (id, name, description, icon) VALUES (?, ?, ?, ?)", categories)

    # Add listings with images from the uploads folder
    images = [
        "/uploads/028219d4-8e07-44b1-a8e9-0d58985e42c8.jpg",
        "/uploads/0d3027d1-1264-4b64-be29-3c3bffd7d3fc.jpg",
        "/uploads/48cd0d8e-7840-4ff9-b9e4-4cf4a1c6f168.jpg",
        "/uploads/79693326-2e8e-4cb3-9766-856b2af92c64.jpg",
    ]

    listings = [
        (str(uuid.uuid4()), "iPhone 15 Pro", "Brand new iPhone", 99999.0, "Active", json.dumps([images[0]]), cat_ids[0], user_id),
        (str(uuid.uuid4()), "Modern Villa", "Luxury villa in suburbs", 15000000.0, "Active", json.dumps([images[1]]), cat_ids[1], user_id),
        (str(uuid.uuid4()), "Tesla Model 3", "Electric car", 4500000.0, "Active", json.dumps([images[2]]), cat_ids[2], user_id),
        (str(uuid.uuid4()), "Designer Watch", "Premium Swiss watch", 12000.0, "Active", json.dumps([images[3]]), cat_ids[3], user_id),
    ]

    cursor.executemany("""
        INSERT INTO listings (id, title, description, price, status, images, category_id, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, listings)

    conn.commit()
    conn.close()
    print("Seed complete!")

if __name__ == "__main__":
    seed()
