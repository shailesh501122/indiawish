import sys
import os
import uuid
import bcrypt

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User

def create_admin():
    db = SessionLocal()
    # Verify tables exist
    Base.metadata.create_all(bind=engine)
    
    admin_email = "admin@indiawish.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    
    if not existing_admin:
        # Standard bcrypt for "admin123"
        hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            hashed_password=hashed,
            first_name="IndiaWish",
            last_name="Admin",
            roles="Admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created successfully: {admin_email} / admin123")
    else:
        # If it exists, make sure it has the Admin role
        if existing_admin.roles != "Admin":
            existing_admin.roles = "Admin"
            db.commit()
            print(f"Updated existing user {admin_email} to Admin role.")
        else:
            print(f"Admin user {admin_email} already exists.")
            
    db.close()

if __name__ == "__main__":
    create_admin()
