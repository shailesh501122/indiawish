from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv

load_dotenv()

# Prioritize PostgreSQL using the provided credentials
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/indiawish")

def create_db_engine(url):
    try:
        if url.startswith("sqlite"):
            return create_engine(url, connect_args={"check_same_thread": False})
        
        # Test postgres connection
        temp_engine = create_engine(url)
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return temp_engine
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        print("Falling back to SQLite (indiawish.db)...")
        sqlite_url = "sqlite:///./indiawish.db"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})

from sqlalchemy import text
engine = create_db_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
