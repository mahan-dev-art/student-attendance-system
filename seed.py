import os
from getpass import getpass
from app import app
from models import db
from models.user import User

with app.app_context():
    username=os.getenv("SEED_ADMIN_USERNAME") or input("Admin username [admin]: ").strip() or "admin"
    password=os.getenv("SEED_ADMIN_PASSWORD") or getpass("Admin password (min 8 chars): ")
    if len(password)<8: raise SystemExit("Password must be at least 8 characters.")
    if User.query.filter_by(username=username).first(): raise SystemExit("Username already exists.")
    user=User(username=username,role="admin"); user.set_password(password); db.session.add(user); db.session.commit(); print(f"Admin '{username}' created successfully.")
