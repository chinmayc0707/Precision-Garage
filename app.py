from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from config import Config
from models import db, User, Vehicle, Service, Complaint, Booking, Feedback
from forms import (
    LoginForm, RegisterForm, VehicleForm, BookingForm,
    ComplaintForm, GeneralComplaintForm, FeedbackForm, UpdateKmsForm,
    CompleteServiceForm, CancelBookingForm
)

app = Flask(__name__)
app.config.from_object(Config)

# Make csrf_token() available in all Jinja templates
app.jinja_env.globals['csrf_token'] = generate_csrf

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# ── Custom Filters ──────────────────────────────────────────────────
@app.template_filter('format_indian')
def format_indian(n):
    try:
        s = str(int(n))
    except (ValueError, TypeError):
        return str(n)
    if len(s) <= 3:
        return s
    res = s[-3:]
    s = s[:-3]
    while len(s) > 2:
        res = s[-2:] + "," + res
        s = s[:-2]
    res = s + "," + res
    return res

# ── Context Processors ──────────────────────────────────────────────
@app.context_processor
def inject_globals():
    pending_mechanics_count = 0
    if current_user.is_authenticated and current_user.role == "mechanic" and current_user.is_verified:
        pending_mechanics_count = User.query.filter_by(role="mechanic", is_verified=False).count()
    return {
        "current_date": datetime.now(),
        "garage_open": Config.GARAGE_OPEN_TIME,
        "garage_close": Config.GARAGE_CLOSE_TIME,
        "pending_mechanics_count": pending_mechanics_count,
    }


# ── Decorators ───────────────────────────────────────────────────────
from functools import wraps

def mechanic_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "mechanic":
            flash("Access denied. Mechanics only.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# ── Public Routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    # Fetch latest feedbacks for testimonials
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(6).all()
    # Stats
    total_services = Service.query.count()
    total_users = User.query.count()
    avg_rating = db.session.query(db.func.avg(Feedback.rating)).scalar() or 0
    total_feedbacks = Feedback.query.count()
    return render_template(
        "index.html",
        feedbacks=feedbacks,
        total_services=total_services,
        total_users=total_users,
        avg_rating=round(avg_rating, 1),
        total_feedbacks=total_feedbacks,
    )


@app.route("/about")
def about():
    total_services = Service.query.count()
    total_users = User.query.count()
    avg_rating = db.session.query(db.func.avg(Feedback.rating)).scalar() or 0
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
    return render_template(
        "about.html",
        total_services=total_services,
        total_users=total_users,
        avg_rating=round(avg_rating, 1),
        feedbacks=feedbacks,
    )


@app.route("/services")
def services():
    service_types = [
        {
            "name": "Full Service",
            "desc": "Complete bumper-to-bumper vehicle inspection and maintenance.",
            "icon": "🔧",
        },
        {
            "name": "Oil Change",
            "desc": "Premium oil replacement with filter change and fluid top-up.",
            "icon": "🛢️",
        },
        {
            "name": "Brake Service",
            "desc": "Brake pad inspection, replacement, and rotor resurfacing.",
            "icon": "🛑",
        },
        {
            "name": "Tire Rotation & Alignment",
            "desc": "Tire balancing, rotation, and precision wheel alignment.",
            "icon": "🔄",
        },
        {
            "name": "Engine Diagnostic",
            "desc": "Full electronic diagnostic scan with detailed reporting.",
            "icon": "📊",
        },
        {
            "name": "AC Service & Repair",
            "desc": "Climate system inspection, gas recharge, and repair.",
            "icon": "❄️",
        },
        {
            "name": "Body Repair & Paint",
            "desc": "Dent removal, panel beating, and professional re-painting.",
            "icon": "🎨",
        },
        {
            "name": "General Checkup",
            "desc": "Quick health check before a long drive or seasonal change.",
            "icon": "✅",
        },
    ]
    return render_template("services.html", service_types=service_types)




# ── Auth Routes ──────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        is_mechanic = form.role.data == "mechanic"
        # Auto-verify if this is the first mechanic (bootstrapping)
        auto_verify = is_mechanic and User.query.filter_by(role="mechanic", is_verified=True).count() == 0

        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            role=form.role.data,
            is_verified=not is_mechanic or auto_verify,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        if is_mechanic and not auto_verify:
            flash(
                "Your mechanic account has been created but requires verification "
                "by an existing service man. You will be able to login once approved.",
                "info",
            )
        elif is_mechanic and auto_verify:
            flash("Account created! As the first service man, you are auto-verified. Please login.", "success")
        else:
            flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Block unverified mechanics
            if user.role == "mechanic" and not user.is_verified:
                flash(
                    "Your mechanic account is pending verification by an existing service man. "
                    "Please wait for approval before logging in.",
                    "warning",
                )
                return render_template("login.html", form=form)
            login_user(user)
            next_page = request.args.get("next")
            flash("Welcome back!", "success")
            if user.role == "mechanic":
                return redirect(next_page or url_for("mechanic_dashboard"))
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ── Dashboard ────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "mechanic":
        return redirect(url_for("mechanic_dashboard"))
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    bookings = Booking.query.join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
        Booking.status.in_(["pending", "confirmed", "cancelled"]),
    ).order_by(Booking.preferred_date.asc()).all()

    # Gather service reminders
    reminders = []
    for vehicle in vehicles:
        latest_service = Service.query.filter_by(vehicle_id=vehicle.id).order_by(
            Service.service_date.desc()
        ).first()
        if latest_service and latest_service.next_service_date:
            is_due = latest_service.is_service_due(vehicle.current_kms)
            reminders.append({
                "vehicle": vehicle,
                "service": latest_service,
                "is_due": is_due,
                "next_date": latest_service.next_service_date,
                "next_kms": latest_service.next_service_kms,
            })

    # Active complaints
    complaints = Complaint.query.join(Service).join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
        Complaint.status != "resolved",
    ).all()

    # Service history
    service_history = Service.query.join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
    ).order_by(Service.service_date.desc()).limit(10).all()

    vehicle_form = VehicleForm()
    update_kms_form = UpdateKmsForm()

    return render_template(
        "dashboard.html",
        vehicles=vehicles,
        bookings=bookings,
        reminders=reminders,
        complaints=complaints,
        service_history=service_history,
        vehicle_form=vehicle_form,
        update_kms_form=update_kms_form,
    )


# ── Vehicle Management ───────────────────────────────────────────────
@app.route("/vehicle/add", methods=["POST"])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        if Vehicle.query.filter_by(registration_no=form.registration_no.data).first():
            flash("Vehicle with this registration already exists.", "warning")
            return redirect(url_for("dashboard"))
        vehicle = Vehicle(
            user_id=current_user.id,
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            registration_no=form.registration_no.data,
            current_kms=form.current_kms.data,
        )
        db.session.add(vehicle)
        db.session.commit()
        flash(f"{vehicle.make} {vehicle.model} added!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    return redirect(url_for("dashboard"))


@app.route("/vehicle/<int:vehicle_id>/update-kms", methods=["POST"])
@login_required
def update_kms(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard"))
    form = UpdateKmsForm()
    if form.validate_on_submit():
        vehicle.current_kms = form.current_kms.data
        db.session.commit()
        flash("Kilometers updated.", "success")
    return redirect(url_for("dashboard"))


# ── Booking ──────────────────────────────────────────────────────────
@app.route("/book", methods=["GET", "POST"])
@login_required
def book_service():
    form = BookingForm()
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    form.vehicle_id.choices = [(v.id, f"{v.make} {v.model} ({v.registration_no})") for v in vehicles]

    if not vehicles:
        flash("Please add a vehicle first.", "warning")
        return redirect(url_for("dashboard"))

    if form.validate_on_submit():
        if not Booking.is_date_available(form.preferred_date.data, Config.MAX_VEHICLES_PER_DAY):
            flash(
                f"Sorry, {form.preferred_date.data.strftime('%B %d, %Y')} is fully booked "
                f"(max {Config.MAX_VEHICLES_PER_DAY} vehicles/day). Please choose another date.",
                "warning",
            )
            return render_template("book.html", form=form)

        booking = Booking(
            vehicle_id=form.vehicle_id.data,
            preferred_date=form.preferred_date.data,
            service_type=form.service_type.data,
            notes=form.notes.data,
        )
        db.session.add(booking)
        db.session.commit()
        flash(
            f"Booking confirmed for {form.preferred_date.data.strftime('%B %d, %Y')}! "
            f"Drop off at {Config.GARAGE_OPEN_TIME} AM, collect at {Config.GARAGE_CLOSE_TIME.replace('18', '6')} PM.",
            "success",
        )
        return redirect(url_for("dashboard"))

    # Get unavailable dates for the calendar
    return render_template("book.html", form=form)


@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_user_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Check ownership
    if booking.vehicle.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard"))

    if booking.status not in ["pending", "confirmed"]:
        flash("You can only cancel pending or confirmed bookings.", "warning")
        return redirect(url_for("dashboard"))

    booking.status = "cancelled"
    db.session.commit()
    flash(f"Booking for {booking.vehicle.make} {booking.vehicle.model} on {booking.preferred_date.strftime('%B %d, %Y')} cancelled successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/date-availability/<date_str>")
@login_required
def check_date_availability(date_str):
    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    count = Booking.count_for_date(check_date)
    available = count < Config.MAX_VEHICLES_PER_DAY
    return jsonify({
        "date": date_str,
        "booked": count,
        "max": Config.MAX_VEHICLES_PER_DAY,
        "available": available,
        "slots_left": Config.MAX_VEHICLES_PER_DAY - count,
    })


# ── Complaints ───────────────────────────────────────────────────────
@app.route("/service/<int:service_id>/complaint", methods=["GET", "POST"])
@login_required
def add_complaint(service_id):
    service = Service.query.get_or_404(service_id)
    # Verify ownership
    if service.vehicle.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard"))

    form = ComplaintForm()
    if form.validate_on_submit():
        complaint = Complaint(
            service_id=service.id,
            part_name=form.part_name.data,
            description=form.description.data,
        )
        db.session.add(complaint)
        db.session.commit()
        flash(f"Complaint for '{form.part_name.data}' registered. It will be addressed at your next service.", "success")
        return redirect(url_for("dashboard"))

    return render_template("complaint.html", form=form, service=service)


@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    if current_user.role == "mechanic":
        return redirect(url_for("mechanic_complaints"))

    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    form = GeneralComplaintForm()
    
    # Populate vehicle choices
    form.vehicle_id.choices = [(v.id, f"{v.make} {v.model} ({v.registration_no})") for v in vehicles]
    
    # Populate service choices for validation
    all_services = Service.query.join(Vehicle).filter(Vehicle.user_id == current_user.id).order_by(Service.service_date.desc()).all()
    form.service_id.choices = [(s.id, f"{s.service_type} ({s.vehicle.make} {s.vehicle.model}) — {s.service_date.strftime('%b %d, %Y')}") for s in all_services]

    if form.validate_on_submit():
        selected_vehicle = Vehicle.query.get(form.vehicle_id.data)
        selected_service = Service.query.get(form.service_id.data)
        
        if not selected_vehicle or selected_vehicle.user_id != current_user.id:
            flash("Invalid vehicle selection.", "danger")
            return redirect(url_for("complaints"))
            
        if not selected_service or selected_service.vehicle_id != selected_vehicle.id:
            flash("Invalid service visit selection.", "danger")
            return redirect(url_for("complaints"))

        complaint = Complaint(
            service_id=selected_service.id,
            part_name=form.part_name.data,
            description=form.description.data,
            status="pending"
        )
        db.session.add(complaint)
        db.session.commit()
        flash(f"Complaint for '{form.part_name.data}' registered successfully.", "success")
        return redirect(url_for("complaints"))

    active_complaints = Complaint.query.join(Service).join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
        Complaint.status.in_(["pending", "scheduled"])
    ).order_by(Complaint.created_at.desc()).all()

    resolved_complaints = Complaint.query.join(Service).join(Vehicle).filter(
        Vehicle.user_id == current_user.id,
        Complaint.status == "resolved"
    ).order_by(Complaint.created_at.desc()).all()

    return render_template(
        "complaints.html",
        form=form,
        active_complaints=active_complaints,
        resolved_complaints=resolved_complaints,
        vehicles=vehicles
    )


@app.route("/api/vehicle/<int:vehicle_id>/services")
@login_required
def get_vehicle_services(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id and current_user.role != "mechanic":
        return jsonify({"error": "Unauthorized"}), 403
    services = Service.query.filter_by(vehicle_id=vehicle.id).order_by(Service.service_date.desc()).all()
    return jsonify([
        {
            "id": s.id,
            "service_type": s.service_type,
            "date": s.service_date.strftime("%Y-%m-%d"),
            "formatted_date": s.service_date.strftime("%B %d, %Y")
        } for s in services
    ])


@app.route("/mechanic/complaints")
@login_required
@mechanic_required
def mechanic_complaints():
    status_filter = request.args.get("status", "all")
    query = Complaint.query.join(Service).join(Vehicle)
    
    if status_filter != "all":
        query = query.filter(Complaint.status == status_filter)
        
    complaints_list = query.order_by(Complaint.created_at.desc()).all()
    
    return render_template(
        "mechanic_complaints.html",
        complaints=complaints_list,
        current_filter=status_filter
    )


@app.route("/mechanic/complaint/<int:complaint_id>/update-status", methods=["POST"])
@login_required
@mechanic_required
def update_complaint_status(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if complaint.status == "resolved":
        flash("Resolved complaints cannot be modified.", "danger")
        return redirect(url_for("mechanic_complaints"))
        
    new_status = request.form.get("status")
    
    if new_status not in ["pending", "scheduled", "resolved"]:
        flash("Invalid status selection.", "danger")
        return redirect(url_for("mechanic_complaints"))
        
    complaint.status = new_status
    db.session.commit()
    
    flash(f"Complaint status for '{complaint.part_name}' updated to {new_status}.", "success")
    return redirect(url_for("mechanic_complaints"))


# ── Feedback ─────────────────────────────────────────────────────────
@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    form = FeedbackForm()
    # Populate service choices
    user_services = Service.query.join(Vehicle).filter(
        Vehicle.user_id == current_user.id
    ).order_by(Service.service_date.desc()).all()
    form.service_id.choices = [(0, "General Feedback")] + [
        (s.id, f"{s.service_type} — {s.service_date.strftime('%b %d, %Y')}") for s in user_services
    ]

    if form.validate_on_submit():
        rating_val = int(form.rating.data)
        if rating_val < 1 or rating_val > 5:
            flash("Please select a rating between 1 and 5.", "warning")
            return render_template("feedback.html", form=form)

        fb = Feedback(
            user_id=current_user.id,
            service_id=form.service_id.data if form.service_id.data != 0 else None,
            rating=rating_val,
            comment=form.comment.data,
        )
        db.session.add(fb)
        db.session.commit()
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("dashboard"))

    return render_template("feedback.html", form=form)




# ── Mechanic / Service Man Routes ────────────────────────────────────


@app.route("/mechanic/dashboard")
@login_required
@mechanic_required
def mechanic_dashboard():
    # Filter bookings if requested
    status_filter = request.args.get("status", "all")
    
    query = Booking.query.order_by(Booking.preferred_date.desc())
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
        
    bookings = query.all()
    
    # Enrich bookings with vehicle complaints count
    enriched_bookings = []
    for booking in bookings:
        complaints = Complaint.query.join(Service).filter(
            Service.vehicle_id == booking.vehicle_id,
            Complaint.status != "resolved"
        ).all()
        enriched_bookings.append({
            "booking": booking,
            "complaints": complaints
        })
        
    return render_template(
        "mechanic_dashboard.html",
        bookings=enriched_bookings,
        current_filter=status_filter
    )


@app.route("/mechanic/booking/<int:booking_id>/confirm")
@login_required
@mechanic_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = "confirmed"
    db.session.commit()
    flash(f"Booking for {booking.vehicle.make} {booking.vehicle.model} confirmed.", "success")
    return redirect(url_for("mechanic_dashboard"))


@app.route("/mechanic/booking/<int:booking_id>/cancel", methods=["GET", "POST"])
@login_required
@mechanic_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # If the booking was previously accepted (confirmed), require a cancellation reason
    if booking.status == "confirmed":
        form = CancelBookingForm()
        if form.validate_on_submit():
            booking.status = "cancelled"
            booking.cancellation_reason = form.cancellation_reason.data
            db.session.commit()
            flash(f"Booking for {booking.vehicle.make} {booking.vehicle.model} has been cancelled with reason: {form.cancellation_reason.data}", "info")
            return redirect(url_for("mechanic_dashboard"))
        return render_template("cancel_booking.html", form=form, booking=booking)
    
    # Otherwise (e.g. pending), cancel immediately
    booking.status = "cancelled"
    db.session.commit()
    flash(f"Booking for {booking.vehicle.make} {booking.vehicle.model} cancelled.", "info")
    return redirect(url_for("mechanic_dashboard"))


@app.route("/mechanic/booking/<int:booking_id>/complete", methods=["GET", "POST"])
@login_required
@mechanic_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    vehicle = booking.vehicle
    
    # Get active complaints for this vehicle
    active_complaints = Complaint.query.join(Service).filter(
        Service.vehicle_id == vehicle.id,
        Complaint.status != "resolved"
    ).all()
    
    form = CompleteServiceForm()
    # Pre-fill KMs at service with current vehicle KMs as a starting point
    if request.method == "GET" and not form.kms_at_service.data:
        form.kms_at_service.data = vehicle.current_kms
        
    if form.validate_on_submit():
        # Validate that kms_at_service >= current kms to prevent rollback
        if form.kms_at_service.data < vehicle.current_kms:
            flash(f"Kilometers cannot be less than the vehicle's last recorded kilometers ({vehicle.current_kms} km).", "warning")
            return render_template("complete_service.html", form=form, booking=booking, complaints=active_complaints)
            
        # Create a new Service record
        service = Service(
            vehicle_id=vehicle.id,
            service_date=datetime.utcnow(),
            kms_at_service=form.kms_at_service.data,
            service_type=booking.service_type.replace('_', ' ').title(),
            notes=form.notes.data,
            cost=form.cost.data
        )
        # Calculate next service dates
        service.calculate_next_service(
            interval_kms=app.config["SERVICE_INTERVAL_KMS"],
            interval_months=app.config["SERVICE_INTERVAL_MONTHS"]
        )
        db.session.add(service)
        
        # Update vehicle current kms
        vehicle.current_kms = form.kms_at_service.data
        
        # Update booking status
        booking.status = "completed"
        
        # Resolve active complaints: link them to this service and mark resolved
        for complaint in active_complaints:
            complaint.status = "resolved"
            
        db.session.commit()
        flash(f"Service completed and logged for {vehicle.make} {vehicle.model}!", "success")
        return redirect(url_for("mechanic_dashboard"))
        
    return render_template("complete_service.html", form=form, booking=booking, complaints=active_complaints)



# ── Mechanic Verification Routes ─────────────────────────────────────
@app.route("/mechanic/verify-requests")
@login_required
@mechanic_required
def verify_requests():
    if not current_user.is_verified:
        flash("You must be a verified mechanic to access this page.", "danger")
        return redirect(url_for("mechanic_dashboard"))
    pending = User.query.filter_by(role="mechanic", is_verified=False).order_by(User.created_at.desc()).all()
    return render_template("verify_mechanics.html", pending=pending)


@app.route("/mechanic/verify/<int:user_id>", methods=["POST"])
@login_required
@mechanic_required
def verify_mechanic(user_id):
    if not current_user.is_verified:
        flash("You must be a verified mechanic to perform this action.", "danger")
        return redirect(url_for("mechanic_dashboard"))
    user = User.query.get_or_404(user_id)
    if user.role != "mechanic" or user.is_verified:
        flash("Invalid verification request.", "warning")
        return redirect(url_for("verify_requests"))
    user.is_verified = True
    user.verified_by = current_user.id
    user.verified_at = datetime.utcnow()
    db.session.commit()
    flash(f"{user.name} has been verified as a service man.", "success")
    return redirect(url_for("verify_requests"))


@app.route("/mechanic/reject/<int:user_id>", methods=["POST"])
@login_required
@mechanic_required
def reject_mechanic(user_id):
    if not current_user.is_verified:
        flash("You must be a verified mechanic to perform this action.", "danger")
        return redirect(url_for("mechanic_dashboard"))
    user = User.query.get_or_404(user_id)
    if user.role != "mechanic" or user.is_verified:
        flash("Invalid rejection request.", "warning")
        return redirect(url_for("verify_requests"))
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f"Registration request from {name} has been rejected.", "info")
    return redirect(url_for("verify_requests"))


# ── App Init ─────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
