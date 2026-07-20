import os
from decimal import Decimal
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from models import db, Patient, Visit, Bill
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

billing_bp = Blueprint("billing", __name__)

@billing_bp.route("/patient/<int:patient_id>/new-bill", methods=["GET", "POST"])
@login_required
def new_bill(patient_id):
    patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()
    recent_visit = Visit.query.filter_by(patient_id=patient.id).order_by(Visit.visit_date.desc()).first()

    if not recent_visit:
        flash("Please create a patient visit before generating a bill.", "warning")
        return redirect(url_for("patients.patient_profile", patient_id=patient.id))

    if request.method == "POST":
        consultation_fee = Decimal(request.form.get("consultation_fee", "0.00") or "0.00")
        medicine_fee = Decimal(request.form.get("medicine_fee", "0.00") or "0.00")
        procedure_fee = Decimal(request.form.get("procedure_fee", "0.00") or "0.00")
        discount = Decimal(request.form.get("discount", "0.00") or "0.00")
        payment_method = request.form.get("payment_method", "Cash")
        status = request.form.get("status", "Paid")
        notes = request.form.get("notes", "").strip()

        subtotal = consultation_fee + medicine_fee + procedure_fee
        total_amount = max(Decimal("0.00"), subtotal - discount)

        bill = Bill(
            visit_id=recent_visit.id,
            consultation_fee=consultation_fee,
            medicine_fee=medicine_fee,
            procedure_fee=procedure_fee,
            discount=discount,
            total_amount=total_amount,
            payment_method=payment_method,
            status=status,
            notes=notes
        )

        db.session.add(bill)
        db.session.commit()

        flash("Invoice generated successfully!", "success")
        return redirect(url_for("billing.view_bill", bill_id=bill.id))

    return render_template("new_bill.html", patient=patient, visit=recent_visit, page_title="Generate Bill")

@billing_bp.route("/bill/<int:bill_id>")
@login_required
def view_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    visit = Visit.query.get(bill.visit_id)
    patient = Patient.query.filter_by(id=visit.patient_id, doctor_id=current_user.id).first_or_404()

    subtotal = (bill.consultation_fee or Decimal("0.00")) + (bill.medicine_fee or Decimal("0.00")) + (bill.procedure_fee or Decimal("0.00"))

    return render_template(
        "view_bill.html",
        bill=bill,
        visit=visit,
        patient=patient,
        subtotal=subtotal,
        page_title=f"Patient Bill #{bill.id}"
    )

@billing_bp.route("/bill/<int:bill_id>/pdf")
@login_required
def bill_pdf(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    visit = Visit.query.get(bill.visit_id)
    patient = Patient.query.filter_by(id=visit.patient_id, doctor_id=current_user.id).first_or_404()
    subtotal = (bill.consultation_fee or Decimal("0.00")) + (bill.medicine_fee or Decimal("0.00")) + (bill.procedure_fee or Decimal("0.00"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("ClinicTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"), alignment=0)
    normal_style = ParagraphStyle("Norm", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#334155"))
    bold_style = ParagraphStyle("BoldN", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=colors.HexColor("#0f172a"))
    header_style = ParagraphStyle("Head", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=colors.HexColor("#0f172a"))

    elements = []

    # 1. Header Bar: Clinic Name + Info
    clinic_info_text = f"<b>{current_user.clinic_name}</b><br/><font size=9 color='#64748b'>Your Health, Our Priority</font>"
    contact_text = f"<font size=9 color='#475569'>{current_user.clinic_address or 'Clinic Address'}<br/>Phone: {current_user.phone}<br/>Email: {current_user.email}</font>"
    
    if current_user.logo:
        logo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], current_user.logo)
        if os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=48, height=48)
                header_table = Table([[img, Paragraph(clinic_info_text, title_style), Paragraph(contact_text, normal_style)]], colWidths=[55, 260, 225])
            except Exception:
                header_table = Table([[Paragraph(clinic_info_text, title_style), Paragraph(contact_text, normal_style)]], colWidths=[315, 225])
        else:
            header_table = Table([[Paragraph(clinic_info_text, title_style), Paragraph(contact_text, normal_style)]], colWidths=[315, 225])
    else:
        header_table = Table([[Paragraph(clinic_info_text, title_style), Paragraph(contact_text, normal_style)]], colWidths=[315, 225])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    # 2. "Patient Bill" Title & Metadata Box
    bill_no = f"BC-2026-{(bill.id):04d}"
    meta_box_data = [
        [Paragraph("<b>Bill No:</b>", normal_style), Paragraph(bill_no, bold_style)],
        [Paragraph("<b>Date:</b>", normal_style), Paragraph(bill.created_at.strftime('%d %b %Y'), normal_style)],
        [Paragraph("<b>Time:</b>", normal_style), Paragraph(bill.created_at.strftime('%I:%M %p'), normal_style)]
    ]
    meta_box_table = Table(meta_box_data, colWidths=[65, 95])
    meta_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#bae6fd")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))

    title_table = Table([[Paragraph("Patient Bill", header_style), meta_box_table]], colWidths=[375, 165])
    title_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(title_table)
    elements.append(Spacer(1, 15))

    # 3. Two Cards: Patient Details & Doctor Details
    pt_details_text = f"<b>Name:</b> {patient.name}<br/><b>Patient ID:</b> {patient.patient_code}<br/><b>Age / Gender:</b> {patient.age or 'N/A'} Years / {patient.gender or 'N/A'}<br/><b>Phone:</b> {patient.phone}"
    doc_details_text = f"<b>Dr. {current_user.name}</b><br/>{current_user.qualification or 'MBBS, MD'}<br/>Reg. No: MMC/2019/12345<br/>Phone: {current_user.phone}"

    cards_data = [
        [
            Paragraph("<b>Patient Details</b><br/>" + pt_details_text, normal_style),
            Paragraph("<b>Doctor Details</b><br/>" + doc_details_text, normal_style)
        ]
    ]
    cards_table = Table(cards_data, colWidths=[265, 265])
    cards_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(cards_table)
    elements.append(Spacer(1, 15))

    # 4. Itemized Table
    items_data = [["Sr. No.", "Description", "Quantity", "Rate (Rs)", "Amount (Rs)"]]
    idx = 1
    if bill.consultation_fee > 0:
        items_data.append([str(idx), "Consultation Fee", "1", f"{bill.consultation_fee:,.2f}", f"{bill.consultation_fee:,.2f}"])
        idx += 1
    if bill.medicine_fee > 0:
        items_data.append([str(idx), "Prescribed Medicines Pack", "1", f"{bill.medicine_fee:,.2f}", f"{bill.medicine_fee:,.2f}"])
        idx += 1
    if bill.procedure_fee > 0:
        items_data.append([str(idx), "Clinical Procedures & Lab Tests", "1", f"{bill.procedure_fee:,.2f}", f"{bill.procedure_fee:,.2f}"])
        idx += 1

    if idx == 1:
        items_data.append(["1", "Doctor Consultation Fee", "1", f"{bill.total_amount:,.2f}", f"{bill.total_amount:,.2f}"])

    item_table = Table(items_data, colWidths=[50, 240, 70, 85, 85])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0f2fe")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 15))

    # 5. Bottom Section: Payment Method + Notes (Left) | Subtotal & Total (Right)
    left_notes_html = f"<b>Payment Method:</b><br/>[{'x' if bill.payment_method=='Cash' else ' '}] Cash &nbsp;&nbsp;&nbsp; [{'x' if bill.payment_method=='UPI' else ' '}] UPI &nbsp;&nbsp;&nbsp; [{'x' if bill.payment_method=='Card' else ' '}] Card<br/><br/><font color='#0284c7'><b>✓ Payment Received. Thank you!</b></font><br/><br/><b>Notes:</b><br/>• {bill.notes or 'Keep this bill for future reference.<br/>• Medicine return not applicable.<br/>• For any queries, contact clinic.'}"
    
    right_calc_data = [
        [Paragraph("Subtotal", normal_style), Paragraph(f"Rs. {subtotal:,.2f}", normal_style)],
        [Paragraph("Discount", normal_style), Paragraph(f"- Rs. {(bill.discount or 0):,.2f}", ParagraphStyle("Disc", parent=normal_style, textColor=colors.HexColor("#10b981")))],
        [Paragraph("<b>Total Amount</b>", bold_style), Paragraph(f"<b>Rs. {bill.total_amount:,.2f}</b>", bold_style)]
    ]
    right_calc_table = Table(right_calc_data, colWidths=[110, 110])
    right_calc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,1), (1,1), 1, colors.HexColor("#2563eb")),
    ]))

    bottom_table = Table([[Paragraph(left_notes_html, normal_style), right_calc_table]], colWidths=[310, 220])
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(bottom_table)
    elements.append(Spacer(1, 30))

    # 6. Signature & Footer Line
    sig_data = [["", f"________________________\nDr. {current_user.name}\nAuthorized Signature"]]
    sig_table = Table(sig_data, colWidths=[330, 200])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (1,0), (1,0), 9),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 15))

    footer_bar_data = [[Paragraph(f"<font color='white'><b>{current_user.clinic_name}</b> &nbsp;|&nbsp; Your Health, Our Priority &nbsp;|&nbsp; Thank You!</font>", ParagraphStyle("Foot", parent=normal_style, alignment=1, textColor=colors.white))]]
    footer_bar_table = Table(footer_bar_data, colWidths=[540])
    footer_bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1e293b")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(footer_bar_table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Patient_Bill_{bill_no}_{patient.name}.pdf",
        mimetype="application/pdf"
    )
