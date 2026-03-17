import argparse
import subprocess
import sys
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User


def ensure_schema() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)


def create_admin(email: str, password: str):
    ensure_schema()
    db = SessionLocal()
    try:
        normalized_email = email.strip().lower()
        existing = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
        if existing:
            print("Admin already exists")
            return
        admin = User(email=normalized_email, hashed_password=get_password_hash(password), role="ADMIN", tenant_id=None)
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
