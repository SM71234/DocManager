import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Safely load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

# Handle Render PostgreSQL URI format (replace postgres:// with postgresql://)
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "docmanager-secure-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = db_url or ("sqlite:///" + os.path.join(BASE_DIR, "instance", "docmanager.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    DOCUMENTS_FOLDER = os.path.join(BASE_DIR, "static", "documents")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf", "doc", "docx"}