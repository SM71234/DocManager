from datetime import date, datetime
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, Patient, Visit, PrescriptionMedicine
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

visits_bp = Blueprint("visits", __name__)

@visits_bp.route("/patient/<int:patient_id>/new-visit", methods=["GET", "POST"])
@login_required
def new_visit(patient_id):
    patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        treatment = request.form.get("treatment", "").strip()
        prescription_text = request.form.get("prescription", "").strip()
        notes = request.form.get("notes", "").strip()
        follow_up_str = request.form.get("follow_up_date", "").strip()

        follow_up_date = datetime.strptime(follow_up_str, "%Y-%m-%d").date() if follow_up_str else None

        visit = Visit(
            patient_id=patient.id,
            visit_date=date.today(),
            reason=reason,
            diagnosis=diagnosis,
            treatment=treatment,
            prescription=prescription_text,
            notes=notes,
            follow_up_date=follow_up_date
        )

        db.session.add(visit)
        db.session.flush()  # obtain visit.id

        # Process structured medicines array
        med_names = request.form.getlist("med_name[]")
        med_dosages = request.form.getlist("med_dosage[]")
        med_freqs = request.form.getlist("med_frequency[]")
        med_durations = request.form.getlist("med_duration[]")
        med_instructions = request.form.getlist("med_instructions[]")

        for i in range(len(med_names)):
            name = med_names[i].strip()
            if name:
                med = PrescriptionMedicine(
                    visit_id=visit.id,
                    medicine_name=name,
                    dosage=med_dosages[i].strip() if i < len(med_dosages) else "",
                    frequency=med_freqs[i].strip() if i < len(med_freqs) else "",
                    duration=med_durations[i].strip() if i < len(med_durations) else "",
                    instructions=med_instructions[i].strip() if i < len(med_instructions) else ""
                )
                db.session.add(med)

        db.session.commit()
        flash("Visit and prescription created successfully!", "success")
        return redirect(url_for("patients.patient_profile", patient_id=patient.id))

    return render_template("new_visit.html", patient=patient, page_title="New Visit & Prescription")

@visits_bp.route("/visit/<int:visit_id>")
@login_required
def visit_details(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.filter_by(id=visit.patient_id, doctor_id=current_user.id).first_or_404()
    return render_template("visit_details.html", visit=visit, patient=patient, page_title="Visit Details")

@visits_bp.route("/edit-visit/<int:visit_id>", methods=["GET", "POST"])
@login_required
def edit_visit(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.filter_by(id=visit.patient_id, doctor_id=current_user.id).first_or_404()

    if request.method == "POST":
        visit.reason = request.form.get("reason", "").strip()
        visit.diagnosis = request.form.get("diagnosis", "").strip()
        visit.treatment = request.form.get("treatment", "").strip()
        visit.prescription = request.form.get("prescription", "").strip()
        visit.notes = request.form.get("notes", "").strip()
        follow_up_str = request.form.get("follow_up_date", "").strip()
        visit.follow_up_date = datetime.strptime(follow_up_str, "%Y-%m-%d").date() if follow_up_str else None

        db.session.commit()
        flash("Visit details updated successfully!", "success")
        return redirect(url_for("visits.visit_details", visit_id=visit.id))

    return render_template("edit_visit.html", visit=visit, patient=patient, page_title="Edit Visit")

@visits_bp.route("/prescription/<int:visit_id>")
@login_required
def prescription_pdf(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.filter_by(id=visit.patient_id, doctor_id=current_user.id).first_or_404()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styling
    title_style = ParagraphStyle("ClinicTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#1e3a8a"), alignment=0)
    subtitle_style = ParagraphStyle("DocSub", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=colors.HexColor("#2563eb"))
    normal_style = ParagraphStyle("Norm", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#334155"))
    header_style = ParagraphStyle("Head", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=colors.HexColor("#1e293b"))

    elements = []

    # Header Header - Clinic & Doctor Info
    clinic_text = f"<b>{current_user.clinic_name}</b>"
    doc_text = f"Dr. {current_user.name} ({current_user.qualification or 'MBBS'})\n{current_user.clinic_address or ''}\nPhone: {current_user.phone}"
    
    elements.append(Paragraph(clinic_text, title_style))
    elements.append(Paragraph(doc_text, normal_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=15))

    # Patient Details Bar
    patient_info = [
        [Paragraph(f"<b>Patient Name:</b> {patient.name}", normal_style), Paragraph(f"<b>Patient ID:</b> {patient.patient_code}", normal_style)],
        [Paragraph(f"<b>Age/Gender:</b> {patient.age or 'N/A'} yrs / {patient.gender or 'N/A'}", normal_style), Paragraph(f"<b>Date:</b> {visit.visit_date.strftime('%d %b %Y')}", normal_style)],
        [Paragraph(f"<b>Blood Group:</b> {patient.blood_group or 'N/A'}", normal_style), Paragraph(f"<b>Phone:</b> {patient.phone}", normal_style)]
    ]
    pt_table = Table(patient_info, colWidths=[270, 270])
    pt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(pt_table)
    elements.append(Spacer(1, 15))

    # Clinical Diagnosis & Reason
    if visit.reason:
        elements.append(Paragraph("<b>Chief Complaint:</b>", header_style))
        elements.append(Paragraph(visit.reason, normal_style))
        elements.append(Spacer(1, 8))

    if visit.diagnosis:
        elements.append(Paragraph("<b>Diagnosis:</b>", header_style))
        elements.append(Paragraph(visit.diagnosis, normal_style))
        elements.append(Spacer(1, 12))

    # Prescription Section (Rx symbol)
    elements.append(Paragraph("<font size=16 color='#2563eb'><b>Rx</b></font>", normal_style))
    elements.append(Spacer(1, 6))

    medicines = visit.medicines
    if medicines:
        med_data = [["#", "Medicine Name", "Dosage", "Frequency", "Duration", "Instructions"]]
        for idx, m in enumerate(medicines, 1):
            med_data.append([
                str(idx),
                m.medicine_name,
                m.dosage or "-",
                m.frequency or "-",
                m.duration or "-",
                m.instructions or "-"
            ])
        med_table = Table(med_data, colWidths=[25, 145, 80, 90, 80, 120])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e40af")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ffffff")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(med_table)
    elif visit.prescription:
        prescription_html = visit.prescription.replace("\n", "<br/>")
        elements.append(Paragraph(prescription_html, normal_style))

    elements.append(Spacer(1, 15))

    if visit.follow_up_date:
        elements.append(Paragraph(f"<b>Follow-up Date:</b> {visit.follow_up_date.strftime('%d %b %Y')}", subtitle_style))
        elements.append(Spacer(1, 15))

    if visit.notes:
        elements.append(Paragraph("<b>Doctor's Advice / Notes:</b>", header_style))
        elements.append(Paragraph(visit.notes, normal_style))
        elements.append(Spacer(1, 20))

    # Doctor Signature Footer
    elements.append(Spacer(1, 30))
    sig_data = [["", f"________________________\nDr. {current_user.name}\n(Authorized Signatory)"]]
    sig_table = Table(sig_data, colWidths=[340, 200])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (1,0), (1,0), 9),
        ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#334155")),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{patient.name}_Prescription_{visit.visit_date}.pdf",
        mimetype="application/pdf"
    )
