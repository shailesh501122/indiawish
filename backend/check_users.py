from sqlalchemy import create_engine, text
import os

DATABASE_URL = "sqlite:///./indiawish.db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT email, first_name, last_name FROM users"))
    users = result.fetchall()
    print(f"Total users: {len(users)}")
    for user in users:
        print(user)
