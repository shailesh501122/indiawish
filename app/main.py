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
