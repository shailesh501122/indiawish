import sqlite3
import json

def seed():
    conn = sqlite3.connect('indiawish.db')
    cursor = conn.cursor()

    # Define filter configs
    mobile_filters = [
        {"key": "brand", "label": "Brand", "type": "select", "options": ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi"]},
        {"key": "storage", "label": "Storage", "type": "select", "options": ["64GB", "128GB", "256GB", "512GB"]}
    ]
    vehicle_filters = [
        {"key": "brand", "label": "Brand", "type": "select", "options": ["Tesla", "Toyota", "Honda", "BMW", "Mercedes", "Ford"]},
        {"key": "fuel_type", "label": "Fuel Type", "type": "select", "options": ["Petrol", "Diesel", "Electric", "Hybrid"]},
        {"key": "transmission", "label": "Transmission", "type": "select", "options": ["Automatic", "Manual"]}
    ]

    # Update categories
    cursor.execute("UPDATE categories SET filter_config = ? WHERE name = 'Mobile'", (json.dumps(mobile_filters),))
    cursor.execute("UPDATE categories SET filter_config = ? WHERE name = 'Vehicles'", (json.dumps(vehicle_filters),))

    # Update listings - find a Car (Tesla Model 3 from seed)
    cursor.execute("SELECT id FROM listings WHERE title LIKE '%Tesla%'")
    tesla_listing = cursor.fetchone()
    if tesla_listing:
        tesla_props = {"brand": "Tesla", "fuel_type": "Electric", "transmission": "Automatic"}
        cursor.execute("UPDATE listings SET properties = ? WHERE id = ?", (json.dumps(tesla_props), tesla_listing[0]))
        print(f"Updated Tesla listing {tesla_listing[0]} with properties.")

    # Add another car for testing
    cursor.execute("SELECT id FROM listings WHERE title LIKE '%iPhone%'")
    iphone_listing = cursor.fetchone()
    if iphone_listing:
        iphone_props = {"brand": "Apple", "storage": "128GB"}
        cursor.execute("UPDATE listings SET properties = ? WHERE id = ?", (json.dumps(iphone_props), iphone_listing[0]))
        print(f"Updated iPhone listing {iphone_listing[0]} with properties.")

    conn.commit()
    conn.close()
    print("Filter configs and listing properties seeded.")

if __name__ == "__main__":
    seed()
