import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///garage.db"  # Fallback for local dev
    )
    # Fix Render/Supabase postgres:// → postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_VEHICLES_PER_DAY = 7
    GARAGE_OPEN_TIME = "10:00"
    GARAGE_CLOSE_TIME = "18:00"
    SERVICE_INTERVAL_KMS = 2000
    SERVICE_INTERVAL_MONTHS = 2
