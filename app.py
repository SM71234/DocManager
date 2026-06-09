from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime
import os
from werkzeug.utils import secure_filename

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import Config
from models import (
    db,
    Doctor,
    Patient,
    Visit,
    Appointment,
    Bill
)
from io import BytesIO

from flask import send_file

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(
    Doctor,
    int(user_id)
)


with app.app_context():
    db.create_all()


@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        clinic_name = request.form["clinic_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        existing_email = Doctor.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already registered!",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_phone = Doctor.query.filter_by(
            phone=phone
        ).first()

        if existing_phone:

            flash(
                "Phone number already registered!",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = generate_password_hash(
            password
        )

        doctor = Doctor(
            name=name,
            clinic_name=clinic_name,
            email=email,
            phone=phone,
            password_hash=hashed_password
        )

        db.session.add(doctor)
        db.session.commit()

        flash(
            "Registration Successful! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
    "register.html",
    page_title="Register"
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        doctor = Doctor.query.filter_by(email=email).first()

        if doctor and check_password_hash(
            doctor.password_hash,
            password
        ):

            login_user(doctor)

            flash(
                "Login Successful!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password",
            "danger"
        )

    return render_template(
    "login.html",
    page_title="Login"
    )


from datetime import date

@app.route("/dashboard")
@login_required
def dashboard():

    total_patients = Patient.query.filter_by(
        doctor_id=current_user.id
    ).count()

    patient_ids = Patient.query.with_entities(
        Patient.id
    ).filter_by(
        doctor_id=current_user.id
    )

    total_visits = Visit.query.filter(
        Visit.patient_id.in_(patient_ids)
    ).count()

    todays_visits = Visit.query.filter(
        Visit.visit_date == date.today(),
        Visit.patient_id.in_(patient_ids)
    ).count()

    follow_ups_today = Visit.query.filter(
        Visit.follow_up_date == date.today(),
        Visit.patient_id.in_(patient_ids)
    ).count()

    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date == date.today()
    ).count()

    today_schedule = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date == date.today()
    ).order_by(
        Appointment.appointment_time.asc()
    ).all()

    recent_patients = Patient.query.filter_by(
        doctor_id=current_user.id
    ).order_by(
        Patient.created_at.desc()
    ).limit(5).all()

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
        page_title="Dashboard"
    )

@app.route("/add-patient", methods=["GET", "POST"])
@login_required
def add_patient():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        age = request.form["age"]
        gender = request.form["gender"]
        address = request.form["address"]

        existing_patient = Patient.query.filter_by(
            doctor_id=current_user.id,
            phone=phone
        ).first()

        if existing_patient:
            flash(
                "Patient already exists in the system.",
                "danger"
            )
            return render_template(
                "patient_exists.html",
                patient=existing_patient,
                page_title="Patient Found"
            )

        last_patient = Patient.query.order_by(
            Patient.id.desc()
        ).first()

        if last_patient:

            next_id = last_patient.id + 1

        else:

            next_id = 1

        patient_code = f"DOC-{next_id:04d}"

        patient = Patient(
            patient_code=patient_code,
            doctor_id=current_user.id,
            name=name,
            phone=phone,
            age=age,
            gender=gender,
            address=address
        )

        db.session.add(patient)
        db.session.commit()

        flash(
            "Patient added successfully!",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template(
    "add_patient.html",
    page_title="Add Patient"
)

@app.route("/search-patient", methods=["GET"])
@login_required
def search_patient():

    query = request.args.get("query", "")

    patients = []

    if query:

        patients = Patient.query.filter(
            Patient.doctor_id == current_user.id,
            (
                Patient.name.ilike(f"%{query}%")
                |
                Patient.phone.ilike(f"%{query}%")
            )
        ).all()

    return render_template(
    "search_patient.html",
    patients=patients,
    page_title="Search Patient"
)

@app.route("/follow-ups")
@login_required
def follow_ups():

    today = date.today()

    patient_ids = Patient.query.with_entities(
        Patient.id
    ).filter_by(
        doctor_id=current_user.id
    )

    visits = Visit.query.filter(
        Visit.follow_up_date.isnot(None),
        Visit.patient_id.in_(patient_ids)
    ).order_by(
        Visit.follow_up_date.asc()
    ).all()

    return render_template(
        "follow_ups.html",
        visits=visits,
        today=today,
        page_title="Follow Ups"
    )

@app.route("/patient/<int:patient_id>")
@login_required
def patient_profile(patient_id):

    patient = Patient.query.filter_by(
        id=patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    visits = Visit.query.filter_by(
        patient_id=patient.id
    ).order_by(
        Visit.visit_date.desc()
    ).all()

    return render_template(
        "patient_profile.html",
        patient=patient,
        visits=visits,
        page_title="Patient Details"
    )

@app.route(
    "/patient/<int:patient_id>/new-visit",
    methods=["GET", "POST"]
)
@login_required
def new_visit(patient_id):

    patient = Patient.query.filter_by(
        id=patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        visit = Visit(

            patient_id=patient.id,

            visit_date=date.today(),

            reason=request.form["reason"],

            diagnosis=request.form["diagnosis"],

            treatment=request.form["treatment"],

            prescription=request.form["prescription"],

            notes=request.form["notes"],

            follow_up_date=(

                datetime.strptime(
                    request.form["follow_up_date"],
                    "%Y-%m-%d"
                ).date()

                if request.form["follow_up_date"]

                else None

            )

        )

        db.session.add(visit)

        db.session.commit()

        flash(
            "Visit added successfully!",
            "success"
        )

        return redirect(
            url_for(
                "patient_profile",
                patient_id=patient.id
            )
        )

    return render_template(
        "new_visit.html",
        patient=patient,
        page_title="New Visit"
    )

@app.route("/visit/<int:visit_id>")
@login_required
def visit_details(visit_id):

    visit = Visit.query.get_or_404(visit_id)

    patient = Patient.query.filter_by(
        id=visit.patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    return render_template(
        "visit_details.html",
        visit=visit,
        patient=patient,
        page_title="Visit Details"
)

@app.route(
    "/prescription/<int:visit_id>"
)
@login_required
def prescription_pdf(visit_id):

    visit = Visit.query.get_or_404(
        visit_id
    )

    patient = Patient.query.filter_by(
        id=visit.patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            current_user.clinic_name,
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            f"Dr. {current_user.name}",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            current_user.qualification or "",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            current_user.clinic_address or "",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"<b>Patient:</b> {patient.name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Patient ID:</b> {patient.patient_code}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date:</b> {visit.visit_date}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
    Paragraph(
        "<b>Diagnosis</b>",
        styles["Heading3"]
    )
    )

    elements.append(
        Paragraph(
            visit.diagnosis or "-",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Paragraph(
            "<b>Treatment</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            visit.treatment or "-",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )
    elements.append(
    Spacer(1, 10)
    )
    elements.append(
        Paragraph(
            "<b>Prescription:</b>",
            styles["Heading3"]
        )
    )

    prescription_text = (
    visit.prescription or ""
    ).replace(
        "\r\n",
        "<br/>"
    ).replace(
        "\n",
        "<br/>"
    )

    elements.append(
        Paragraph(
            prescription_text,
            styles["Normal"]
        )
    )
    elements.append(
    Spacer(1, 15)
    )

    elements.append(
        Paragraph(
            "________________________",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Dr. {current_user.name}",
            styles["Normal"]
        )
    )
    elements.append(
    Spacer(1, 15)
    )

    elements.append(
        Paragraph(
            "<b>Doctor Notes</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            visit.notes or "-",
            styles["Normal"]
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{patient.name}_Prescription.pdf",
        mimetype="application/pdf"
    )

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

    if request.method == "POST":

        current_user.name = request.form["name"]

        current_user.clinic_name = request.form["clinic_name"]

        new_phone = request.form["phone"]

        existing_phone = Doctor.query.filter(
            Doctor.phone == new_phone,
            Doctor.id != current_user.id
        ).first()

        if existing_phone:

            flash(
                "Phone number already in use.",
                "danger"
            )

            return redirect(
                url_for("settings")
            )

        current_user.phone = new_phone

        new_email = request.form["email"]

        existing_doctor = Doctor.query.filter(
            Doctor.email == new_email,
            Doctor.id != current_user.id
        ).first()

        if existing_doctor:

            flash(
                "Email already in use by another account.",
                "danger"
            )

            return redirect(
                url_for("settings")
            )

        current_user.email = new_email

        current_user.clinic_address = request.form[
            "clinic_address"
        ]

        current_user.qualification = request.form[
        "qualification"
        ]

        logo = request.files.get("logo")

        if logo and logo.filename:

            filename = secure_filename(
                logo.filename
            )

            logo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            current_user.logo = filename

        db.session.commit()

        flash(
            "Settings updated successfully!",
            "success"
        )

        return redirect(
            url_for("settings")
        )

    return render_template(
        "settings.html",
        page_title="Settings"
    )


@app.route("/edit-patient/<int:patient_id>",
           methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):

    patient = Patient.query.filter_by(
        id=patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        patient.name = request.form["name"]
        patient.phone = request.form["phone"]
        patient.age = request.form["age"]
        patient.gender = request.form["gender"]
        patient.address = request.form["address"]

        db.session.commit()

        flash("Patient updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "patient_profile",
                patient_id=patient.id
            )
        )

    return render_template(
        "edit_patient.html",
        patient=patient
    )

@app.route("/edit-visit/<int:visit_id>",
           methods=["GET", "POST"])
@login_required
def edit_visit(visit_id):

    visit = Visit.query.get_or_404(visit_id)

    patient = Patient.query.filter_by(
        id=visit.patient_id,
        doctor_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        visit.reason = request.form["reason"]
        visit.diagnosis = request.form["diagnosis"]
        visit.treatment = request.form["treatment"]
        visit.prescription = request.form["prescription"]
        visit.notes = request.form["notes"]

        db.session.commit()

        flash(
            "Visit updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "visit_details",
                visit_id=visit.id
            )
        )

    return render_template(
        "edit_visit.html",
        visit=visit,
        patient=patient
    )

@app.route(
    "/bill/new/<int:visit_id>",
    methods=["GET", "POST"]
)
@login_required
def new_bill(visit_id):

    visit = Visit.query.get_or_404(visit_id)

    patient = Patient.query.get_or_404(
        visit.patient_id
    )

    if request.method == "POST":

        consultation_fee = float(
            request.form["consultation_fee"] or 0
        )

        medicine_fee = float(
            request.form["medicine_fee"] or 0
        )

        procedure_fee = float(
            request.form["procedure_fee"] or 0
        )

        total_amount = (
            consultation_fee +
            medicine_fee +
            procedure_fee
        )

        bill = Bill(
            visit_id=visit.id,
            consultation_fee=consultation_fee,
            medicine_fee=medicine_fee,
            procedure_fee=procedure_fee,
            total_amount=total_amount
        )

        db.session.add(bill)
        db.session.commit()

        flash(
            "Bill generated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "view_bill",
                bill_id=bill.id
            )
        )

    return render_template(
        "new_bill.html",
        visit=visit,
        patient=patient
    )

@app.route("/bill/<int:bill_id>")
@login_required
def view_bill(bill_id):

    bill = Bill.query.get_or_404(
        bill_id
    )

    visit = Visit.query.get(
        bill.visit_id
    )

    patient = Patient.query.get(
        visit.patient_id
    )

    return render_template(
        "view_bill.html",
        bill=bill,
        visit=visit,
        patient=patient
    )
@app.route(
    "/bill/pdf/<int:bill_id>"
)
@login_required
def bill_pdf(bill_id):

    bill = Bill.query.get_or_404(
        bill_id
    )

    visit = Visit.query.get(
        bill.visit_id
    )

    patient = Patient.query.get(
        visit.patient_id
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            current_user.clinic_name,
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            f"Dr. {current_user.name}",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            current_user.qualification or "",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            current_user.clinic_address or "",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 25))

    elements.append(
        Paragraph(
            "<b>INVOICE</b>",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            f"<b>Patient Name:</b> {patient.name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Patient ID:</b> {patient.patient_code}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date:</b> {visit.visit_date}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<b>Billing Details</b>",
            styles["Heading3"]
        )
    )

    elements.append(
        Paragraph(
            f"Consultation Fee ............ Rs. {bill.consultation_fee:.2f}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Medicine Charges ............ Rs. {bill.medicine_fee:.2f}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Procedure Charges ........... Rs. {bill.procedure_fee:.2f}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            f"<b>Total Amount: Rs. {bill.total_amount:.2f}</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 40))

    elements.append(
        Paragraph(
            "Thank you for visiting.",
            styles["Italic"]
        )
    )

    elements.append(Spacer(1, 40))

    elements.append(
        Paragraph(
            "__________________________",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Dr. {current_user.name}",
            styles["Normal"]
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Invoice_{patient.patient_code}.pdf",
        mimetype="application/pdf"
    )

@app.route("/appointments")
@login_required
def appointments():

    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()

    return render_template(
        "appointments.html",
        appointments=appointments,
        page_title="Appointments"
    )

@app.route(
    "/appointments/new",
    methods=["GET", "POST"]
)
@login_required
def new_appointment():

    patients = Patient.query.filter_by(
        doctor_id=current_user.id
    ).all()

    if request.method == "POST":

        appointment = Appointment(

            doctor_id=current_user.id,

            patient_id=request.form["patient_id"],

            appointment_date=datetime.strptime(
                request.form["appointment_date"],
                "%Y-%m-%d"
            ).date(),

            appointment_time=datetime.strptime(
                request.form["appointment_time"],
                "%H:%M"
            ).time(),

            notes=request.form["notes"],

            status="Scheduled"
        )

        db.session.add(appointment)

        db.session.commit()

        flash(
            "Appointment created successfully!",
            "success"
        )

        return redirect(
            url_for("appointments")
        )

    return render_template(
        "new_appointment.html",
        patients=patients,
        page_title="New Appointment"
    )

@app.route(
    "/appointment/<int:appointment_id>/complete"
)
@login_required
def complete_appointment(appointment_id):

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()

    appointment.status = "Completed"

    db.session.commit()

    flash(
        "Appointment marked as completed.",
        "success"
    )

    return redirect(
        url_for("appointments")
    )


@app.route(
    "/appointment/<int:appointment_id>/cancel"
)
@login_required
def cancel_appointment(appointment_id):

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()

    appointment.status = "Cancelled"

    db.session.commit()

    flash(
        "Appointment cancelled.",
        "warning"
    )

    return redirect(
        url_for("appointments")
    )

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Logged Out Successfully",
        "success"
    )

    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)