import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_endpoint(path):
    try:
        r = requests.get(f"{BASE_URL}{path}")
        print(f"GET {path}: {r.status_code}")
        if r.status_code != 200:
            print(f"Error: {r.text}")
        else:
            data = r.json()
            print(f"Items returned: {len(data) if isinstance(data, list) else 'Object'}")
            if isinstance(data, list) and len(data) > 0:
                print(f"First item keys: {data[0].keys()}")
    except Exception as e:
        print(f"GET {path} FAILED: {e}")

test_endpoint("/listings/home/fresh")
test_endpoint("/listings/categories")
