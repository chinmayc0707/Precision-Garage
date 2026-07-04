from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="customer") # customer, mechanic
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicles = db.relationship("Vehicle", backref="owner", lazy=True, cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.name}>"


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    make = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    registration_no = db.Column(db.String(20), unique=True, nullable=False)
    current_kms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    services = db.relationship("Service", backref="vehicle", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="vehicle", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.registration_no})>"


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    service_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    kms_at_service = db.Column(db.Integer, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)  # e.g. "Full Service", "Oil Change"
    notes = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)

    # Next service thresholds
    next_service_date = db.Column(db.DateTime, nullable=True)
    next_service_kms = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    complaints = db.relationship("Complaint", backref="service", lazy=True, cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", backref="service", lazy=True)

    def calculate_next_service(self, interval_kms=2000, interval_months=2):
        """Auto-calculate next service date and kms."""
        self.next_service_kms = self.kms_at_service + interval_kms
        self.next_service_date = self.service_date + timedelta(days=interval_months * 30)

    def is_service_due(self, current_kms):
        """Check if service is due based on kms or date."""
        now = datetime.utcnow()
        kms_due = self.next_service_kms and current_kms >= self.next_service_kms
        date_due = self.next_service_date and now >= self.next_service_date
        return kms_due or date_due

    def __repr__(self):
        return f"<Service {self.service_type} on {self.service_date}>"


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    part_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, scheduled, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Complaint {self.part_name} — {self.status}>"


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, completed, cancelled
    cancellation_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def count_for_date(date):
        """Count confirmed + pending bookings for a given date."""
        return Booking.query.filter(
            Booking.preferred_date == date,
            Booking.status.in_(["pending", "confirmed"])
        ).count()

    @staticmethod
    def is_date_available(date, max_vehicles=7):
        """Check if the date still has capacity."""
        return Booking.count_for_date(date) < max_vehicles

    def __repr__(self):
        return f"<Booking {self.preferred_date} — {self.status}>"


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.rating}★ by User {self.user_id}>"




class Newsletter(db.Model):
    __tablename__ = "newsletters"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Newsletter {self.email}>"
