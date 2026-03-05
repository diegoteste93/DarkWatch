import argparse
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User


def create_admin(email: str, password: str):
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            print("Admin already exists")
            return
        admin = User(email=email, hashed_password=get_password_hash(password), role="admin", tenant_id=None)
        db.add(admin)
        db.commit()
        print("Admin created")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    create_admin(args.email, args.password)
