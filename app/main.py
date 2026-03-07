from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import traceback
import os
from .api.endpoints import auth, marketplace, properties, ai, users, admin, chat, config, escrow
from .routers import upload
from .db.session import engine, Base
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
    try:
        with engine.connect() as conn:
            # 1. FIX USERS TABLE
            try:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
                columns = [row[0] for row in result]
                if 'verification_level' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_level VARCHAR DEFAULT 'unverified';"))
                if 'is_elite' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_elite BOOLEAN DEFAULT FALSE;"))
                if 'last_seen' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;"))
                conn.commit()
            except Exception as e:
                print(f"Users table migration error: {e}")
            
            # 2. FIX LISTINGS TABLE
            try:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'listings'"))
                columns = [row[0] for row in result]
                if 'properties' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN properties JSONB DEFAULT '{}';"))
                if 'location' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN location VARCHAR;"))
                if 'listing_type' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN listing_type VARCHAR DEFAULT 'sell';"))
                if 'rent_price' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN rent_price FLOAT;"))
                if 'rent_period' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN rent_period VARCHAR;"))
                if 'video_url' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN video_url VARCHAR;"))
                if 'subcategory_id' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN subcategory_id VARCHAR;"))
                if 'subcategory' not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN subcategory VARCHAR;"))
                conn.commit()
            except Exception as e:
                print(f"Listings table migration error: {e}")

            # 3. FIX CATEGORIES TABLE
            try:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories'"))
                columns = [row[0] for row in result]
                if 'filter_config' not in columns:
                    conn.execute(text("ALTER TABLE categories ADD COLUMN filter_config JSONB DEFAULT '[]';"))
                if 'subcategories' not in columns:
                    conn.execute(text("ALTER TABLE categories ADD COLUMN subcategories JSONB DEFAULT '[]';"))
                conn.commit()
            except Exception as e:
                print(f"Categories table migration error: {e}")
            
            # 4. FIX PROPERTIES TABLE
            try:
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'properties'"))
                columns = [row[0] for row in result]
                if 'active_status' not in columns:
                    conn.execute(text("ALTER TABLE properties ADD COLUMN active_status BOOLEAN DEFAULT TRUE;"))
                conn.commit()
            except Exception as e:
                print(f"Properties table migration error: {e}")

            print("Migration: All schema checks completed.")
    except Exception as e:
        print(f"Migration error: {e}")

fix_all_schemas()

# CORS configuration – allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
