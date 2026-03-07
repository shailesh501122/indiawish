from sqlalchemy import create_engine, text
import os

DATABASE_URL = "sqlite:///./indiawish.db"
engine = create_engine(DATABASE_URL)

email = "john@example.com"
new_roles = "User,Admin"

with engine.connect() as conn:
    # Update the user's roles
    result = conn.execute(
        text("UPDATE users SET roles = :roles WHERE email = :email"),
        {"roles": new_roles, "email": email}
    )
    conn.commit()
    print(f"Updated roles for {email} to {new_roles}")

    # Verify the change
    result = conn.execute(
        text("SELECT email, roles FROM users WHERE email = :email"),
        {"email": email}
    )
    user = result.fetchone()
    print(f"Verification: {user}")
