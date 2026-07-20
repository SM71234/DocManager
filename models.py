from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Doctor(UserMixin, db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    clinic_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    clinic_address = db.Column(db.Text)
    qualification = db.Column(db.String(100))
    logo = db.Column(db.String(255))
    
    # WhatsApp Integration Credentials
    whatsapp_enabled = db.Column(db.Boolean, default=False)
    whatsapp_phone_id = db.Column(db.String(100))
    whatsapp_access_token = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=utc_now)

    patients = db.relationship("Patient", backref="doctor", lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", backref="doctor", lazy=True, cascade="all, delete-orphan")


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(30), unique=True, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False, index=True)
    email = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    medical_history = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)

    visits = db.relationship("Visit", backref="patient", lazy=True, cascade="all, delete-orphan", order_by="desc(Visit.visit_date)")
    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")
    documents = db.relationship("PatientDocument", backref="patient", lazy=True, cascade="all, delete-orphan")


class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)

    visit_date = db.Column(db.Date, nullable=False, index=True)
    reason = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    medicines = db.relationship("PrescriptionMedicine", backref="visit", lazy=True, cascade="all, delete-orphan")
    bill = db.relationship("Bill", backref="visit", uselist=False, cascade="all, delete-orphan")


class PrescriptionMedicine(db.Model):
    __tablename__ = "prescription_medicines"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False, index=True)
    medicine_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    instructions = db.Column(db.Text)


class PatientDocument(db.Model):
    __tablename__ = "patient_documents"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # bytes
    uploaded_at = db.Column(db.DateTime, default=utc_now)


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)

    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default="Scheduled")  # Scheduled, Completed, Cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False, index=True)

    consultation_fee = db.Column(db.Numeric(10, 2), default=0.00)
    medicine_fee = db.Column(db.Numeric(10, 2), default=0.00)
    procedure_fee = db.Column(db.Numeric(10, 2), default=0.00)
    discount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    payment_method = db.Column(db.String(30), default="Cash")  # Cash, UPI, Card
    status = db.Column(db.String(20), default="Paid")  # Paid, Pending
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)