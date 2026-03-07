from app.db.session import SessionLocal
from app.models.user import User

def check_users():
    db = SessionLocal()
    users = db.query(User).all()
    print("Email | Roles")
    for u in users:
        print(f"{u.email} | {u.roles}")
    db.close()

if __name__ == "__main__":
    check_users()
