from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/indiawish")
SQLITE_URL = "sqlite:///./indiawish.db"

def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except:
        return create_engine(SQLITE_URL)

engine = get_engine()

def add_column(table, column, type):
    try:
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type}"))
            conn.commit()
            print(f"Added column {column} to {table}")
    except Exception as e:
        print(f"Column {column} in {table} might already exist: {e}")

# Columns to add
add_column("users", "created_at", "TIMESTAMP")
add_column("users", "updated_at", "TIMESTAMP")
add_column("users", "active_status", "BOOLEAN DEFAULT TRUE")
add_column("users", "last_seen", "TIMESTAMP")
add_column("users", "is_elite", "BOOLEAN DEFAULT FALSE")

# Ensure all tables mentioned in models are created
from app.db.session import engine as db_engine, Base
from app.models.user import User, Follower
from app.models.marketplace import Listing, Category, Property, ListingInteraction, SubCategory
from app.models.chat import Conversation, Message

Base.metadata.create_all(bind=db_engine)
print("Base.metadata.create_all(bind=db_engine) executed")


# Tables and other columns should be created by Base.metadata.create_all if they don't exist
