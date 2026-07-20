from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Patient, Appointment

appointments_bp = Blueprint("appointments", __name__)

@appointments_bp.route("/appointments")
@login_required
def appointments():
    filter_status = request.args.get("status", "All")
    view_mode = request.args.get("view", "calendar")  # calendar or list

    query = Appointment.query.filter_by(doctor_id=current_user.id)

    if filter_status and filter_status != "All":
        query = query.filter(Appointment.status == filter_status)

    appointments_list = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()
    patients = Patient.query.filter_by(doctor_id=current_user.id).order_by(Patient.name.asc()).all()

    return render_template(
        "appointments.html",
        appointments=appointments_list,
        patients=patients,
        filter_status=filter_status,
        view_mode=view_mode,
        today=date.today(),
        page_title="Appointments Calendar"
    )

@appointments_bp.route("/new-appointment", methods=["GET", "POST"])
@login_required
def new_appointment():
    patients = Patient.query.filter_by(doctor_id=current_user.id).order_by(Patient.name.asc()).all()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        appt_date_str = request.form.get("appointment_date")
        appt_time_str = request.form.get("appointment_time")
        notes = request.form.get("notes", "").strip()

        if not patient_id or not appt_date_str or not appt_time_str:
            flash("Please select a patient, date, and time.", "danger")
            return redirect(url_for("appointments.new_appointment"))

        appt_date = datetime.strptime(appt_date_str, "%Y-%m-%d").date()
        appt_time = datetime.strptime(appt_time_str, "%H:%M").time()

        appointment = Appointment(
            doctor_id=current_user.id,
            patient_id=int(patient_id),
            appointment_date=appt_date,
            appointment_time=appt_time,
            notes=notes,
            status="Scheduled"
        )

        db.session.add(appointment)
        db.session.commit()

        flash("Appointment scheduled successfully!", "success")
        return redirect(url_for("appointments.appointments"))

    return render_template("new_appointment.html", patients=patients, page_title="Schedule Appointment")

@appointments_bp.route("/appointment/<int:appointment_id>/complete")
@login_required
def complete_appointment(appointment_id):
    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=current_user.id).first_or_404()
    appointment.status = "Completed"
    db.session.commit()
    flash("Appointment marked as Completed.", "success")
    return redirect(url_for("appointments.appointments"))

@appointments_bp.route("/appointment/<int:appointment_id>/cancel")
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=current_user.id).first_or_404()
    appointment.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled.", "warning")
    return redirect(url_for("appointments.appointments"))
