from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from models import Patient, Appointment, Visit

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/global-search")
@login_required
def global_search():
    q = request.args.get("q", "").strip()
    results = []

    # System Quick Navigation Items
    pages = [
        {"title": "Dashboard", "category": "Navigation", "url": url_for("patients.dashboard"), "icon": "bi-speedometer2"},
        {"title": "Add New Patient", "category": "Action", "url": url_for("patients.add_patient"), "icon": "bi-person-plus"},
        {"title": "Search Patients", "category": "Navigation", "url": url_for("patients.search_patient"), "icon": "bi-search"},
        {"title": "Schedule Appointment", "category": "Action", "url": url_for("appointments.new_appointment"), "icon": "bi-calendar-plus"},
        {"title": "Appointments Calendar", "category": "Navigation", "url": url_for("appointments.appointments"), "icon": "bi-calendar-event"},
        {"title": "Follow-ups", "category": "Navigation", "url": url_for("patients.follow_ups"), "icon": "bi-clock-history"},
        {"title": "Analytics & Reports", "category": "Navigation", "url": url_for("analytics.analytics_dashboard"), "icon": "bi-bar-chart"},
        {"title": "Settings & Profile", "category": "Navigation", "url": url_for("settings.settings"), "icon": "bi-gear"}
    ]

    if not q:
        return jsonify(pages[:6])

    # Filter navigation pages
    for p in pages:
        if q.lower() in p["title"].lower():
            results.append(p)

    # Search Patients
    patients = Patient.query.filter_by(doctor_id=current_user.id).filter(
        (Patient.name.ilike(f"%{q}%")) |
        (Patient.phone.ilike(f"%{q}%")) |
        (Patient.patient_code.ilike(f"%{q}%"))
    ).limit(5).all()

    for p in patients:
        results.append({
            "title": f"{p.name} ({p.patient_code})",
            "category": "Patient",
            "subtitle": f"Phone: {p.phone} | Age: {p.age or 'N/A'}",
            "url": url_for("patients.patient_profile", patient_id=p.id),
            "icon": "bi-person"
        })

    return jsonify(results)

@api_bp.route("/api/calendar-events")
@login_required
def calendar_events():
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
    events = []
    for a in appointments:
        patient = Patient.query.get(a.patient_id)
        events.append({
            "id": a.id,
            "title": f"{patient.name if patient else 'Patient'} ({a.appointment_time.strftime('%I:%M %p')})",
            "start": f"{a.appointment_date}T{a.appointment_time}",
            "status": a.status,
            "patient_name": patient.name if patient else "Unknown",
            "notes": a.notes or "",
            "url": url_for("patients.patient_profile", patient_id=a.patient_id) if patient else "#"
        })
    return jsonify(events)
