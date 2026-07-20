import os
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Patient, Visit, Appointment, Bill, PatientDocument

patients_bp = Blueprint("patients", __name__)

@patients_bp.route("/dashboard")
@login_required
def dashboard():
    total_patients = Patient.query.filter_by(doctor_id=current_user.id).count()
    patient_ids = [p.id for p in Patient.query.with_entities(Patient.id).filter_by(doctor_id=current_user.id).all()]

    total_visits = Visit.query.filter(Visit.patient_id.in_(patient_ids)).count() if patient_ids else 0
    todays_visits = Visit.query.filter(Visit.visit_date == date.today(), Visit.patient_id.in_(patient_ids)).count() if patient_ids else 0
    follow_ups_today = Visit.query.filter(Visit.follow_up_date == date.today(), Visit.patient_id.in_(patient_ids)).count() if patient_ids else 0

    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date == date.today()
    ).count()

    today_schedule = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date == date.today()
    ).order_by(Appointment.appointment_time.asc()).all()

    recent_patients = Patient.query.filter_by(doctor_id=current_user.id).order_by(Patient.created_at.desc()).limit(5).all()

    # Overdue follow-ups
    overdue_followups = Visit.query.filter(
        Visit.follow_up_date < date.today(),
        Visit.patient_id.in_(patient_ids)
    ).order_by(Visit.follow_up_date.desc()).limit(5).all() if patient_ids else []

    return render_template(
        "dashboard.html",
        doctor=current_user,
        total_patients=total_patients,
        total_visits=total_visits,
        todays_visits=todays_visits,
        follow_ups_today=follow_ups_today,
        recent_patients=recent_patients,
        today_appointments=today_appointments,
        today_schedule=today_schedule,
        overdue_followups=overdue_followups,
        page_title="Dashboard"
    )

@patients_bp.route("/add-patient", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_group = request.form.get("blood_group")
        medical_history = request.form.get("medical_history")
        emergency_contact = request.form.get("emergency_contact")
        address = request.form.get("address")

        if not name or not phone:
            flash("Patient Name and Phone Number are required.", "danger")
            return redirect(url_for("patients.add_patient"))

        existing_patient = Patient.query.filter_by(
            doctor_id=current_user.id,
            phone=phone
        ).first()

        if existing_patient:
            flash("Patient with this phone number already exists.", "danger")
            return render_template("patient_exists.html", patient=existing_patient, page_title="Patient Found")

        # Atomic/safe patient code generation
        last_patient = Patient.query.order_by(Patient.id.desc()).first()
        next_id = (last_patient.id + 1) if last_patient else 1
        patient_code = f"DOC-{next_id:04d}"

        patient = Patient(
            patient_code=patient_code,
            doctor_id=current_user.id,
            name=name,
            phone=phone,
            email=email,
            age=int(age) if age and age.isdigit() else None,
            gender=gender,
            blood_group=blood_group,
            medical_history=medical_history,
            emergency_contact=emergency_contact,
            address=address
        )

        db.session.add(patient)
        db.session.commit()

        flash(f"Patient {patient.name} ({patient.patient_code}) added successfully!", "success")
        return redirect(url_for("patients.patient_profile", patient_id=patient.id))

    return render_template("add_patient.html", page_title="Add Patient")

@patients_bp.route("/edit-patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

    if request.method == "POST":
        patient.name = request.form.get("name", "").strip()
        patient.phone = request.form.get("phone", "").strip()
        patient.email = request.form.get("email", "").strip()
        age = request.form.get("age")
        patient.age = int(age) if age and age.isdigit() else None
        patient.gender = request.form.get("gender")
        patient.blood_group = request.form.get("blood_group")
        patient.medical_history = request.form.get("medical_history")
        patient.emergency_contact = request.form.get("emergency_contact")
        patient.address = request.form.get("address")

        db.session.commit()
        flash("Patient profile updated successfully!", "success")
        return redirect(url_for("patients.patient_profile", patient_id=patient.id))

    return render_template("edit_patient.html", patient=patient, page_title="Edit Patient")

@patients_bp.route("/search-patient", methods=["GET"])
@login_required
def search_patient():
    query = request.args.get("query", "").strip()
    gender_filter = request.args.get("gender", "")
    blood_filter = request.args.get("blood_group", "")

    patients_query = Patient.query.filter_by(doctor_id=current_user.id)

    if query:
        patients_query = patients_query.filter(
            (Patient.name.ilike(f"%{query}%")) |
            (Patient.phone.ilike(f"%{query}%")) |
            (Patient.patient_code.ilike(f"%{query}%")) |
            (Patient.email.ilike(f"%{query}%"))
        )

    if gender_filter:
        patients_query = patients_query.filter(Patient.gender == gender_filter)

    if blood_filter:
        patients_query = patients_query.filter(Patient.blood_group == blood_filter)

    patients = patients_query.order_by(Patient.created_at.desc()).all()

    return render_template("search_patient.html", patients=patients, query=query, page_title="Search Patients")

@patients_bp.route("/patient/<int:patient_id>")
@login_required
def patient_profile(patient_id):
    patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()
    visits = Visit.query.filter_by(patient_id=patient.id).order_by(Visit.visit_date.desc()).all()
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appointment_date.desc()).all()
    documents = PatientDocument.query.filter_by(patient_id=patient.id).order_by(PatientDocument.uploaded_at.desc()).all()
    
    # Financial bills list
    visit_ids = [v.id for v in visits]
    bills = Bill.query.filter(Bill.visit_id.in_(visit_ids)).all() if visit_ids else []

    active_tab = request.args.get("tab", "overview")

    return render_template(
        "patient_profile.html",
        patient=patient,
        visits=visits,
        appointments=appointments,
        documents=documents,
        bills=bills,
        active_tab=active_tab,
        page_title=f"Patient: {patient.name}"
    )

@patients_bp.route("/patient/<int:patient_id>/upload-document", methods=["POST"])
@login_required
def upload_document(patient_id):
    patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()
    doc_file = request.files.get("document")
    title = request.form.get("title", "").strip() or "Lab Report / Document"

    if doc_file and doc_file.filename:
        filename = secure_filename(doc_file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S_")
        saved_filename = f"{timestamp}{filename}"
        file_path = os.path.join(current_app.config["DOCUMENTS_FOLDER"], saved_filename)
        doc_file.save(file_path)

        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(filename)[1].lower()

        doc_record = PatientDocument(
            patient_id=patient.id,
            title=title,
            file_name=saved_filename,
            file_type=file_ext,
            file_size=file_size
        )
        db.session.add(doc_record)
        db.session.commit()

        flash("Document uploaded successfully!", "success")

    return redirect(url_for("patients.patient_profile", patient_id=patient.id, tab="documents"))

@patients_bp.route("/documents/<path:filename>")
@login_required
def view_document(filename):
    return send_from_directory(current_app.config["DOCUMENTS_FOLDER"], filename)

@patients_bp.route("/follow-ups")
@login_required
def follow_ups():
    today = date.today()
    patient_ids = [p.id for p in Patient.query.with_entities(Patient.id).filter_by(doctor_id=current_user.id).all()]

    visits = Visit.query.filter(
        Visit.follow_up_date.isnot(None),
        Visit.patient_id.in_(patient_ids)
    ).order_by(Visit.follow_up_date.asc()).all() if patient_ids else []

    return render_template(
        "follow_ups.html",
        visits=visits,
        today=today,
        page_title="Follow-up Reminders"
    )
