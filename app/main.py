from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import traceback
import os
from .api.endpoints import auth, marketplace, properties, ai, users, admin, chat, config, escrow, discovery, services
from .routers import upload
from .db.session import engine, Base
from .models import services as services_models
from fastapi_socketio import SocketManager

app = FastAPI(
    title="IndiaWish API",
    description="Python FastAPI backend replacing the .NET Core implementation.",
    version="1.0.0"
)

# Initialize SocketManager
# Note: Using '*' for allowed origins to bypass strict browser/client checks for development/mobile
socket_manager = SocketManager(app=app, cors_allowed_origins="*")

# Create database tables
Base.metadata.create_all(bind=engine)

# Comprehensive Fix for missing columns (Automated Migration)
def fix_all_schemas():
    from sqlalchemy import text
    
    def add_column_if_missing(conn, table, column, type_def):
        try:
            # Try to add the column. If it exists, SQL will throw an error we catch.
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_def};"))
            conn.commit()
            print(f"Migration: Added {column} to {table}")
        except Exception:
            # Column likely already exists or table doesn't exist yet
            pass

    try:
        with engine.connect() as conn:
            # Define all missing columns to check/add
            # For SQLite, we use simple types (VARCHAR, BOOLEAN). 
            # For PostgreSQL, these map correctly too.
            
            # Users
            add_column_if_missing(conn, "users", "verification_level", "VARCHAR DEFAULT 'unverified'")
            add_column_if_missing(conn, "users", "is_elite", "BOOLEAN DEFAULT FALSE")
            add_column_if_missing(conn, "users", "last_seen", "TIMESTAMP WITH TIME ZONE")
            
            # Listings
            add_column_if_missing(conn, "listings", "properties", "JSONB DEFAULT '{}'")
            add_column_if_missing(conn, "listings", "location", "VARCHAR")
            add_column_if_missing(conn, "listings", "listing_type", "VARCHAR DEFAULT 'sell'")
            add_column_if_missing(conn, "listings", "rent_price", "FLOAT")
            add_column_if_missing(conn, "listings", "rent_period", "VARCHAR")
            add_column_if_missing(conn, "listings", "video_url", "VARCHAR")
            add_column_if_missing(conn, "listings", "subcategory_id", "VARCHAR")
            add_column_if_missing(conn, "listings", "subcategory", "VARCHAR")
            add_column_if_missing(conn, "listings", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # Categories
            add_column_if_missing(conn, "categories", "filter_config", "JSONB DEFAULT '[]'")
            add_column_if_missing(conn, "categories", "subcategories", "JSONB DEFAULT '[]'")
            add_column_if_missing(conn, "categories", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # Subcategories
            add_column_if_missing(conn, "subcategories", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # Properties
            add_column_if_missing(conn, "properties", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # System Config table creation
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        key VARCHAR PRIMARY KEY,
                        value TEXT NOT NULL,
                        description VARCHAR
                    );
                """))
                conn.commit()
            except Exception: pass

            print("Migration: All schema checks completed.")
    except Exception as e:
        print(f"Migration error: {e}")

# Fix for missing categories (Auto-Seed)
def seed_dynamic_data():
    from app.models.marketplace import Category
    from app.models.config import SystemConfig
    from app.db.session import SessionLocal
    import uuid
    
    db = SessionLocal()
    try:
        # 1. Categories
        if db.query(Category).count() == 0:
            print("Migration: Seeding default categories...")
            default_cats = [
                {"id": "ebd6634a-6b63-4e5b-9a0e-ea1c691d3fc7", "name": "Vehicles", "icon": "directions_car", "description": "Cars and bikes"},
                {"id": "5b1893f3-3b50-4857-92f4-679d7ecb2bbf", "name": "Services", "icon": "work", "description": "Rentals and services"},
                {"id": str(uuid.uuid4()), "name": "Mobile", "icon": "smartphone", "description": "Phones and tablets"},
                {"id": str(uuid.uuid4()), "name": "Electronics", "icon": "kitchen", "description": "Gadgets and tech"},
                {"id": str(uuid.uuid4()), "name": "Real Estate", "icon": "home", "description": "Properties and land"},
                {"id": str(uuid.uuid4()), "name": "Fashion", "icon": "checkroom", "description": "Clothes and accessories"},
            ]
            for cat in default_cats:
                db.add(Category(
                    id=cat["id"],
                    name=cat["name"],
                    icon=cat["icon"],
                    description=cat["description"],
                    active_status=True
                ))
            db.commit()

        # 2. System Config
        if db.query(SystemConfig).count() == 0:
            print("Migration: Seeding default system configuration...")
            configs = [
                {"key": "app_name", "value": "IndiaWish", "description": "Display name of the application"},
                {"key": "search_hint", "value": "Find Cars, Mobile Phones and more...", "description": "Hint text for home search bar"},
                {"key": "primary_color", "value": "0xFF002F5F", "description": "Primary brand color (hex)"},
                {"key": "secondary_color", "value": "0xFF7F8C8D", "description": "Secondary brand color"},
                {"key": "support_email", "value": "support@indiawish.com", "description": "Contact email"},
            ]
            for cfg in configs:
                db.add(SystemConfig(**cfg))
            db.commit()
            
    except Exception as e:
        print(f"Seeding error: {e}")
    finally:
        db.close()

fix_all_schemas()
seed_dynamic_data()

# CORS configuration
origins = [
    "https://indiawishadmin.vercel.app",
    "https://indiawish-admin.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Socket.io Events
@app.sio.on('join_room')
async def handle_join(sid, data):
    # data expected: {'room': 'conversation_id', 'token': 'jwt_token'}
    # In a real app, verify token here
    room = data.get('room')
    if room:
        app.sio.enter_room(sid, room)
        print(f"SID {sid} joined room {room}")

@app.sio.on('leave_room')
async def handle_leave(sid, data):
    room = data.get('room')
    if room:
        app.sio.leave_room(sid, room)
        print(f"SID {sid} left room {room}")

@app.sio.on('connect')
async def handle_connect(sid, environ):
    print(f"Connected: {sid}")

@app.sio.on('disconnect')
async def handle_disconnect(sid):
    print(f"Disconnected: {sid}")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(marketplace.router, prefix="/api/listings", tags=["marketplace"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(escrow.router, prefix="/api/escrow", tags=["escrow"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
# Static files for uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global exception caught: {exc}\n{traceback.format_exc()}\n"
    print(error_msg)
    with open("error_log.txt", "a") as f:
        f.write(error_msg)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": str(exc)
        }
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to IndiaWish Python API"}
