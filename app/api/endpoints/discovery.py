from ...db.session import get_db
from ...models.config import SystemConfig
from sqlalchemy.orm import Session

router = APIRouter()

def get_google_maps_api_key(db: Session) -> str:
    """Helper to fetch API key from DB or Env."""
    # Priority 1: Check Database (manageable via Admin Panel)
    config = db.query(SystemConfig).filter(SystemConfig.key == "google_maps_api_key").first()
    if config and config.value:
        return config.value
    # Priority 2: Check Environment Variable
    return os.getenv("GOOGLE_MAPS_API_KEY", "")

@router.get("/nearby")
async def get_nearby_places(
    lat: float,
    lng: float,
    category: str = "tourist_attraction",
    radius: int = 5000,
    db: Session = Depends(get_db)
):
    """Proxies Google Places API to find nearby places."""
    api_key = get_google_maps_api_key(db)
    if not api_key:
        return get_mock_places(category)

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": category,
        "key": api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return get_mock_places(category)
            
        results = []
        for item in data.get("results", []):
            photo_ref = ""
            if item.get("photos"):
                photo_ref = item["photos"][0].get("photo_reference", "")
            
            results.append({
                "id": item.get("place_id"),
                "name": item.get("name"),
                "rating": item.get("rating", 0.0),
                "address": item.get("vicinity"),
                "image_url": f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={api_key}" if photo_ref else "https://via.placeholder.com/400x300?text=No+Image",
                "category": category.replace("_", " ").title(),
                "distance": "Nearby"
            })
        return results

@router.get("/autocomplete")
async def autocomplete_location(input: str, db: Session = Depends(get_db)):
    """Search for locations using Google Places Autocomplete."""
    api_key = get_google_maps_api_key(db)
    if not api_key:
        # Mock search results for India
        all_mocks = [
            {"id": "p1", "description": "New Delhi, Delhi, India"},
            {"id": "p2", "description": "Mumbai, Maharashtra, India"},
            {"id": "p3", "description": "Bangalore, Karnataka, India"},
            {"id": "p4", "description": "Hyderabad, Telangana, India"},
            {"id": "p5", "description": "Chennai, Tamil Nadu, India"},
            {"id": "p6", "description": "Pune, Maharashtra, India"},
        ]
        return [m for m in all_mocks if input.lower() in m["description"].lower()]

    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input,
        "components": "country:in",  # Restrict to India
        "key": api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        predictions = []
        for p in data.get("predictions", []):
            predictions.append({
                "id": p.get("place_id"),
                "description": p.get("description")
            })
        return predictions

@router.get("/details")
async def get_place_details(place_id: str, db: Session = Depends(get_db)):
    """Get lat/lng for a specific place_id."""
    api_key = get_google_maps_api_key(db)
    if not api_key:
        # Mock details
        coords = {
            "p1": {"lat": 28.6139, "lng": 77.2090},
            "p2": {"lat": 19.0760, "lng": 72.8777},
        }
        res = coords.get(place_id, {"lat": 28.6139, "lng": 77.2090})
        return res

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "geometry",
        "key": api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        location = data.get("result", {}).get("geometry", {}).get("location", {})
        return {
            "lat": location.get("lat"),
            "lng": location.get("lng")
        }

def get_mock_places(category: str):
    # Fallback mock data if no API key is provided
    mocks = {
        "restaurant": [
            {"id": "m1", "name": "Gulati Restaurant", "rating": 4.5, "address": "Pandara Road, Delhi", "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4", "category": "Restaurant", "distance": "1.2 km"},
            {"id": "m2", "name": "Bukhara", "rating": 4.8, "address": "ITC Maurya, Chanakyapuri", "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9", "category": "Restaurant", "distance": "3.5 km"}
        ],
        "hotel": [
            {"id": "h1", "name": "The Taj Mahal Hotel", "rating": 4.9, "address": "Mansingh Road, Delhi", "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945", "category": "Hotel", "distance": "0.8 km"},
            {"id": "h2", "name": "Oberoi Gurgaon", "rating": 4.7, "address": "Udyog Vihar, Gurgaon", "image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb", "category": "Hotel", "distance": "5.2 km"}
        ],
        "movie_theater": [
            {"id": "mov1", "name": "PVR Director's Cut", "rating": 4.6, "address": "Ambience Mall, Vasant Kunj", "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba", "category": "Cinema", "distance": "4.1 km"}
        ],
        "tourist_attraction": [
            {"id": "t1", "name": "India Gate", "rating": 4.7, "address": "Rajpath, New Delhi", "image_url": "https://images.unsplash.com/photo-1587474260584-136574528ed5", "category": "Tourist Place", "distance": "2.1 km"},
            {"id": "t2", "name": "Qutub Minar", "rating": 4.5, "address": "Mehrauli, New Delhi", "image_url": "https://images.unsplash.com/photo-1524492707947-52a818c4d291", "category": "Tourist Place", "distance": "8.4 km"}
        ]
    }
    return mocks.get(category.lower(), mocks["restaurant"])
