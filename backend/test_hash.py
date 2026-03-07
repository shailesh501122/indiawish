from app.core.security import get_password_hash, verify_password

try:
    p = "Password123"
    h = get_password_hash(p)
    print(f"Password: {p}")
    print(f"Hash: {h}")
    print(f"Verify: {verify_password(p, h)}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
