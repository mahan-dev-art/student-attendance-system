import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'attendance.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ESP32_API_KEY = os.getenv("ESP32_API_KEY", "development-api-key")
    WTF_CSRF_TIME_LIMIT = None
