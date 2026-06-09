from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Doctor(UserMixin, db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    clinic_name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    phone = db.Column(db.String(15), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    clinic_address = db.Column(db.Text)
    qualification = db.Column(
        db.String(100)
    )
    patients = db.relationship(
        "Patient",
        backref="doctor",
        lazy=True
    )
    appointments = db.relationship(
        "Appointment",
        backref="doctor",
        lazy=True,
        cascade="all, delete-orphan"
    )   
    logo = db.Column(   
        db.String(255)
    )


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(
        db.String(20),
        unique=True
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(15),
        nullable=False,
        index=True
    )

    age = db.Column(db.Integer)

    gender = db.Column(db.String(20))

    address = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    visits = db.relationship(
        "Visit",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )
    appointments = db.relationship(
        "Appointment",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )

class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    visit_date = db.Column(
        db.Date,
        nullable=False
    )

    reason = db.Column(db.Text)

    diagnosis = db.Column(db.Text)

    treatment = db.Column(db.Text)

    prescription = db.Column(db.Text)

    notes = db.Column(db.Text)

    follow_up_date = db.Column(
        db.Date,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    bill = db.relationship(
        "Bill",
        backref="visit",
        uselist=False,
        cascade="all, delete-orphan"
    )

class PrescriptionMedicine(db.Model):
    __tablename__ = "prescription_medicines"
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    visit_id = db.Column(
        db.Integer,
        db.ForeignKey("visits.id")
    )

    medicine_name = db.Column(
        db.String(200)
    )

    dosage = db.Column(
        db.String(100)
    )

    frequency = db.Column(
        db.String(100)
    )

    duration = db.Column(
        db.String(100)
    )
    
class Appointment(db.Model):

    __tablename__ = "appointments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    appointment_date = db.Column(
        db.Date,
        nullable=False
    )

    appointment_time = db.Column(
        db.Time,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Scheduled"
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Bill(db.Model):

    __tablename__ = "bills"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    visit_id = db.Column(
        db.Integer,
        db.ForeignKey("visits.id"),
        nullable=False
    )

    consultation_fee = db.Column(
        db.Float,
        default=0
    )

    medicine_fee = db.Column(
        db.Float,
        default=0
    )

    procedure_fee = db.Column(
        db.Float,
        default=0
    )

    total_amount = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )