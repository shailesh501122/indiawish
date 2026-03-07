import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

def test_register():
    print("Testing Registration...")
    payload = {
        "firstName": "Test",
        "lastName": "User",
        "email": "testuser@example.com",
        "password": "Password123",
        "phoneNumber": "1234567890"
    }
    try:
        response = requests.post(f"{BASE_URL}/register", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_login():
    print("\nTesting Login...")
    payload = {
        "email": "testuser@example.com",
        "password": "Password123"
    }
    try:
        response = requests.post(f"{BASE_URL}/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_register()
    test_login()
