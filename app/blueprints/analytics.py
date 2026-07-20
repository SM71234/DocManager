from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, Patient, Visit, Appointment, Bill

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def analytics_dashboard():
    return render_template("analytics.html", page_title="Analytics & Reports")

@analytics_bp.route("/api/analytics-data")
@login_required
def analytics_data():
    patient_ids = [p.id for p in Patient.query.with_entities(Patient.id).filter_by(doctor_id=current_user.id).all()]

    # Last 7 Days Visits & Revenue
    today = date.today()
    labels = []
    visit_counts = []
    revenue_sums = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%a (%d %b)")
        labels.append(day_str)

        if patient_ids:
            v_cnt = Visit.query.filter(Visit.visit_date == day, Visit.patient_id.in_(patient_ids)).count()
            # Revenue from bills on this date
            day_bills = Bill.query.join(Visit).filter(Visit.visit_date == day, Visit.patient_id.in_(patient_ids)).all()
            rev = sum(float(b.total_amount or 0) for b in day_bills)
        else:
            v_cnt = 0
            rev = 0.0

        visit_counts.append(v_cnt)
        revenue_sums.append(rev)

    # Demographics: Gender Breakdown
    male_cnt = Patient.query.filter_by(doctor_id=current_user.id, gender="Male").count()
    female_cnt = Patient.query.filter_by(doctor_id=current_user.id, gender="Female").count()
    other_cnt = Patient.query.filter_by(doctor_id=current_user.id).filter(Patient.gender.notin_(["Male", "Female"])).count()

    # Top Diagnoses
    diagnoses_raw = [v.diagnosis for v in Visit.query.filter(Visit.patient_id.in_(patient_ids)).all() if v.diagnosis] if patient_ids else []
    diagnosis_counts = {}
    for d in diagnoses_raw:
        clean_d = d.strip().capitalize()
        diagnosis_counts[clean_d] = diagnosis_counts.get(clean_d, 0) + 1

    sorted_diag = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_diag_labels = [x[0] for x in sorted_diag] if sorted_diag else ["General Checkup", "Fever", "Hypertension"]
    top_diag_counts = [x[1] for x in sorted_diag] if sorted_diag else [10, 5, 3]

    return jsonify({
        "labels": labels,
        "visits": visit_counts,
        "revenue": revenue_sums,
        "gender": [male_cnt, female_cnt, other_cnt],
        "top_diagnoses_labels": top_diag_labels,
        "top_diagnoses_data": top_diag_counts
    })
