from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

DATABASE_URL = "sqlite:///./indiawish.db"
engine = create_engine(DATABASE_URL)

email = "john@example.com"
password = "admin123"
hashed_password = get_password_hash(password)

with engine.connect() as conn:
    # Update the user's password
    result = conn.execute(
        text("UPDATE users SET hashed_password = :hp WHERE email = :email"),
        {"hp": hashed_password, "email": email}
    )
    conn.commit()
    print(f"Updated password for {email} to {password}")

    # Verify the change
    result = conn.execute(
        text("SELECT email, hashed_password FROM users WHERE email = :email"),
        {"email": email}
    )
    user = result.fetchone()
    print(f"Verification: {user}")
