from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Doctor

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("patients.dashboard"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("patients.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        clinic_name = request.form.get("clinic_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not name or not clinic_name or not email or not phone or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register"))

        if Doctor.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("auth.register"))

        if Doctor.query.filter_by(phone=phone).first():
            flash("Phone number already registered!", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)
        doctor = Doctor(
            name=name,
            clinic_name=clinic_name,
            email=email,
            phone=phone,
            password_hash=hashed_password
        )

        db.session.add(doctor)
        db.session.commit()

        flash("Registration Successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", page_title="Register")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("patients.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        doctor = Doctor.query.filter_by(email=email).first()

        if doctor and check_password_hash(doctor.password_hash, password):
            login_user(doctor, remember=remember)
            flash("Welcome back, Dr. " + doctor.name + "!", "success")
            return redirect(url_for("patients.dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html", page_title="Login")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged Out Successfully", "success")
    return redirect(url_for("auth.login"))
