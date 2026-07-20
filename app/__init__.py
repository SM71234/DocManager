import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from config import Config
from models import db, Doctor

login_manager = LoginManager()
migrate = Migrate()

def auto_migrate_db(app):
    with app.app_context():
        inspector = inspect(db.engine)
        
        # 1. Auto-add missing columns to 'patients' table
        if "patients" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("patients")]
            with db.engine.begin() as conn:
                if "email" not in columns:
                    conn.execute(text("ALTER TABLE patients ADD COLUMN email VARCHAR(120)"))
                if "blood_group" not in columns:
                    conn.execute(text("ALTER TABLE patients ADD COLUMN blood_group VARCHAR(10)"))
                if "medical_history" not in columns:
                    conn.execute(text("ALTER TABLE patients ADD COLUMN medical_history TEXT"))
                if "emergency_contact" not in columns:
                    conn.execute(text("ALTER TABLE patients ADD COLUMN emergency_contact VARCHAR(100)"))

        # 2. Auto-add missing columns to 'bills' table
        if "bills" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("bills")]
            with db.engine.begin() as conn:
                if "status" not in columns:
                    conn.execute(text("ALTER TABLE bills ADD COLUMN status VARCHAR(20) DEFAULT 'Paid'"))
                if "discount" not in columns:
                    conn.execute(text("ALTER TABLE bills ADD COLUMN discount NUMERIC(10,2) DEFAULT 0.00"))
                if "payment_method" not in columns:
                    conn.execute(text("ALTER TABLE bills ADD COLUMN payment_method VARCHAR(30) DEFAULT 'Cash'"))
                if "notes" not in columns:
                    conn.execute(text("ALTER TABLE bills ADD COLUMN notes TEXT"))

        # 3. Auto-add missing columns to 'prescription_medicines' table
        if "prescription_medicines" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("prescription_medicines")]
            with db.engine.begin() as conn:
                if "instructions" not in columns:
                    conn.execute(text("ALTER TABLE prescription_medicines ADD COLUMN instructions TEXT"))

        # 4. Auto-add missing columns to 'doctors' table
        if "doctors" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("doctors")]
            with db.engine.begin() as conn:
                if "clinic_address" not in columns:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN clinic_address TEXT"))
                if "qualification" not in columns:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN qualification VARCHAR(100)"))
                if "logo" not in columns:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN logo VARCHAR(255)"))

        # Create any remaining missing tables
        db.create_all()

def create_app(config_class=Config):
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["DOCUMENTS_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "danger"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Doctor, int(user_id))

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.patients import patients_bp
    from app.blueprints.visits import visits_bp
    from app.blueprints.appointments import appointments_bp
    from app.blueprints.billing import billing_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(visits_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)

    auto_migrate_db(app)

    return app
