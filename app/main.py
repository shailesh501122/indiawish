from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import traceback
import os
from .api.endpoints import auth, marketplace, properties, ai, users, admin, chat, config, escrow, discovery, services, notifications
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
    from sqlalchemy import text, inspect
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Migration: Checking tables: {tables}")
        
        with engine.begin() as conn:
            # Helper to add column if missing
            def ensure_column(table_name, column_name, type_def):
                if table_name not in tables:
                    return
                columns = [c['name'] for c in inspector.get_columns(table_name)]
                if column_name not in columns:
                    print(f"Migration: Adding {column_name} to {table_name}...")
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {type_def}"))
                else:
                    # print(f"Migration: {table_name}.{column_name} already exists.")
                    pass

            # Users
            ensure_column("users", "verification_level", "VARCHAR DEFAULT 'unverified'")
            ensure_column("users", "is_elite", "BOOLEAN DEFAULT FALSE")
            ensure_column("users", "last_seen", "TIMESTAMP WITH TIME ZONE")
            ensure_column("users", "referral_code", "VARCHAR")
            ensure_column("users", "referred_by_id", "VARCHAR")
            ensure_column("users", "referral_reward_balance", "FLOAT DEFAULT 0.0")
            
            # Listings
            ensure_column("listings", "properties", "JSONB DEFAULT '{}'")
            ensure_column("listings", "location", "VARCHAR")
            ensure_column("listings", "listing_type", "VARCHAR DEFAULT 'sell'")
            ensure_column("listings", "rent_price", "FLOAT")
            ensure_column("listings", "rent_period", "VARCHAR")
            ensure_column("listings", "video_url", "VARCHAR")
            ensure_column("listings", "subcategory_id", "VARCHAR")
            ensure_column("listings", "subcategory", "VARCHAR")
            ensure_column("listings", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # Categories
            ensure_column("categories", "filter_config", "JSONB DEFAULT '[]'")
            ensure_column("categories", "subcategories", "JSONB DEFAULT '[]'")
            ensure_column("categories", "active_status", "BOOLEAN DEFAULT TRUE")
            ensure_column("categories", "whatsapp_contact_enabled", "BOOLEAN DEFAULT TRUE")
            
            # Subcategories
            ensure_column("subcategories", "active_status", "BOOLEAN DEFAULT TRUE")
            ensure_column("subcategories", "icon", "VARCHAR")
            ensure_column("subcategories", "category_id", "VARCHAR")
            
            # Properties
            ensure_column("properties", "active_status", "BOOLEAN DEFAULT TRUE")
            
            # Service Categories
            ensure_column("service_categories", "active_status", "BOOLEAN DEFAULT TRUE")
            ensure_column("service_categories", "icon", "VARCHAR")
            
            # Service Profiles
            ensure_column("service_profiles", "active_status", "BOOLEAN DEFAULT TRUE")
            ensure_column("service_profiles", "is_verified", "BOOLEAN DEFAULT FALSE")
            
            # System Config table creation (if not exists)
            if "system_config" not in tables:
                print("Migration: Creating system_config table...")
                conn.execute(text("""
                    CREATE TABLE system_config (
                        key VARCHAR PRIMARY KEY,
                        value TEXT NOT NULL,
                        description VARCHAR
                    );
                """))

            # Notifications
            ensure_column("notifications", "is_read", "BOOLEAN DEFAULT FALSE")
            ensure_column("notifications", "data", "JSONB")

            # --- INDEXES FOR PERFORMANCE ---
            def ensure_index(index_name, table_name, columns):
                try:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"))
                except:
                    pass

            ensure_index("idx_listings_active_status", "listings", "active_status")
            ensure_index("idx_listings_status", "listings", "status")
            ensure_index("idx_listings_created_at", "listings", "created_at")
            ensure_index("idx_service_profiles_active_status", "service_profiles", "active_status")
            ensure_index("idx_listing_interactions_listing_id", "listing_interactions", "listing_id")
            ensure_index("idx_listing_interactions_user_id", "listing_interactions", "user_id")
            ensure_index("idx_listing_interactions_created_at", "listing_interactions", "created_at")

            print("Migration: All schema checks and index optimizations completed successfully.")
    except Exception as e:
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()

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

        # 3. Service Categories (Requirement 4)
        from app.models.services import ServiceCategory
        if db.query(ServiceCategory).count() == 0:
            print("Migration: Seeding default service categories...")
            service_cats = [
                {"name": "Housemaid", "icon": "cleaning_services", "description": "Professional house cleaning"},
                {"name": "Cook/Chef", "icon": "soup_kitchen", "description": "Home cooked meals and catering"},
                {"name": "Plumber", "icon": "plumbing", "description": "Pipe repairs and installation"},
                {"name": "Electrician", "icon": "electrical_services", "description": "Wiring and electrical repairs"},
            ]
            for sc in service_cats:
                db.add(ServiceCategory(**sc))
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
app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
# Static files for uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Run custom migrations and seed data on startup
@app.on_event("startup")
async def startup_event():
    print("Migration: Starting startup schema checks...")
    fix_all_schemas()
    seed_dynamic_data()

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
