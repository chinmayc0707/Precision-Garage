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
    BASE_VEHICLES_SERVICED = int(os.environ.get("BASE_VEHICLES_SERVICED", 1250))
    BASE_HAPPY_CLIENTS = int(os.environ.get("BASE_HAPPY_CLIENTS", 340))
    YEARS_EXPERIENCE = int(os.environ.get("YEARS_EXPERIENCE", 8))
    try:
        UPCOMING_BOOKINGS_LIMIT = int(os.environ.get("UPCOMING_BOOKINGS_LIMIT", 5))
    except (ValueError, TypeError):
        UPCOMING_BOOKINGS_LIMIT = 5

