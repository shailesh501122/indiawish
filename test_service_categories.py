import requests
import os

BASE_URL = "http://localhost:8000/api"
# Assuming an admin token is available or can be obtained.
# For verification, we might need to skip auth or use a test token.
# In this environment, I'll check if I can hit the endpoint.

def test_crud():
    print("Testing Service Category CRUD...")
    
    # 1. GET (should be empty or have seeded data)
    r = requests.get(f"{BASE_URL}/admin/service-categories")
    print(f"GET /admin/service-categories: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Found {len(data)} categories")

    # 2. POST (Create)
    cat_data = {"name": "Test Category", "description": "Test Description"}
    r = requests.post(f"{BASE_URL}/admin/service-categories", data=cat_data)
    print(f"POST /admin/service-categories: {r.status_code}")
    if r.status_code == 200:
        cat_id = r.json()["id"]
        print(f"Created category with ID: {cat_id}")
        
        # 3. PUT (Update)
        update_data = {"name": "Updated Test Category", "active_status": "false"}
        r = requests.put(f"{BASE_URL}/admin/service-categories/{cat_id}", data=update_data)
        print(f"PUT /admin/service-categories/{cat_id}: {r.status_code}")
        
        # 4. DELETE
        r = requests.delete(f"{BASE_URL}/admin/service-categories/{cat_id}")
        print(f"DELETE /admin/service-categories/{cat_id}: {r.status_code}")

if __name__ == "__main__":
    test_crud()
