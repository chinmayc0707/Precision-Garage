from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, IntegerField,
    SelectField, DateField, HiddenField, FloatField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
)
from datetime import date


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    role = SelectField("Role", choices=[("customer", "Customer"), ("mechanic", "Service Man / Mechanic")], default="customer")
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )


class VehicleForm(FlaskForm):
    make = StringField("Make (e.g. BMW, Toyota)", validators=[DataRequired(), Length(max=80)])
    model = StringField("Model (e.g. M3, Corolla)", validators=[DataRequired(), Length(max=80)])
    year = IntegerField("Year", validators=[Optional(), NumberRange(min=1900, max=2030)])
    registration_no = StringField("Registration Number", validators=[DataRequired(), Length(max=20)])
    current_kms = IntegerField("Current Kilometers", validators=[DataRequired(), NumberRange(min=0)])


class BookingForm(FlaskForm):
    vehicle_id = SelectField("Select Vehicle", coerce=int, validators=[DataRequired()])
    preferred_date = DateField("Preferred Date", validators=[DataRequired()])
    service_type = SelectField(
        "Service Type",
        choices=[
            ("full_service", "Full Service"),
            ("oil_change", "Oil Change"),
            ("brake_service", "Brake Service"),
            ("tire_rotation", "Tire Rotation & Alignment"),
            ("engine_diagnostic", "Engine Diagnostic"),
            ("ac_service", "AC Service & Repair"),
            ("body_repair", "Body Repair & Paint"),
            ("general_checkup", "General Checkup"),
        ],
        validators=[DataRequired()]
    )
    notes = TextAreaField("Additional Notes", validators=[Optional(), Length(max=500)])

    def validate_preferred_date(self, field):
        if field.data < date.today():
            raise ValidationError("Cannot book a date in the past.")


class ComplaintForm(FlaskForm):
    part_name = StringField("Part Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Describe the Issue", validators=[DataRequired(), Length(max=1000)])


class GeneralComplaintForm(FlaskForm):
    vehicle_id = SelectField("Select Vehicle", coerce=int, validators=[DataRequired()])
    service_id = SelectField("Select Service Visit", coerce=int, validators=[DataRequired()])
    part_name = StringField("Part Name / Component", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Describe the Issue", validators=[DataRequired(), Length(max=1000)])



class FeedbackForm(FlaskForm):
    service_id = SelectField("Select Service (optional)", coerce=int, validators=[Optional()])
    rating = HiddenField("Rating", validators=[DataRequired()])
    comment = TextAreaField("Your Feedback", validators=[Optional(), Length(max=1000)])


class UpdateKmsForm(FlaskForm):
    current_kms = IntegerField("Current Kilometers", validators=[DataRequired(), NumberRange(min=0)])


class CompleteServiceForm(FlaskForm):
    kms_at_service = IntegerField("KMs at Service", validators=[DataRequired(), NumberRange(min=0)])
    cost = FloatField("Service Cost", validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField("Mechanic Service Notes", validators=[Optional(), Length(max=1000)])


class CancelBookingForm(FlaskForm):
    cancellation_reason = TextAreaField("Reason for Cancellation", validators=[DataRequired(), Length(min=5, max=1000)])



class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])

class VerifyOTPForm(FlaskForm):
    otp = StringField("OTP", validators=[DataRequired(), Length(min=6, max=6)])

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
