import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Doctor

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip()
        current_user.clinic_name = request.form.get("clinic_name", "").strip()

        new_phone = request.form.get("phone", "").strip()
        existing_phone = Doctor.query.filter(Doctor.phone == new_phone, Doctor.id != current_user.id).first()
        if existing_phone:
            flash("Phone number is already in use by another account.", "danger")
            return redirect(url_for("settings.settings"))
        current_user.phone = new_phone

        new_email = request.form.get("email", "").strip().lower()
        existing_email = Doctor.query.filter(Doctor.email == new_email, Doctor.id != current_user.id).first()
        if existing_email:
            flash("Email address is already in use by another account.", "danger")
            return redirect(url_for("settings.settings"))
        current_user.email = new_email

        current_user.clinic_address = request.form.get("clinic_address", "").strip()
        current_user.qualification = request.form.get("qualification", "").strip()

        # WhatsApp Integration Credentials
        current_user.whatsapp_enabled = bool(request.form.get("whatsapp_enabled"))
        current_user.whatsapp_phone_id = request.form.get("whatsapp_phone_id", "").strip()
        current_user.whatsapp_access_token = request.form.get("whatsapp_access_token", "").strip()

        logo = request.files.get("logo")
        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            ext = os.path.splitext(filename)[1].lower().lstrip(".")
            if ext in current_app.config["ALLOWED_EXTENSIONS"]:
                saved_filename = f"logo_{current_user.id}_{filename}"
                logo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], saved_filename))
                current_user.logo = saved_filename
            else:
                flash("Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP", "warning")

        db.session.commit()
        flash("Settings & WhatsApp configuration updated successfully!", "success")
        return redirect(url_for("settings.settings"))

    return render_template("settings.html", page_title="Settings & Profile")
