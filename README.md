# 🩺 DocManager — Intelligent Healthcare Management System

[![Flask](https://img.shields.io/badge/Flask-3.0.0-blue?logo=flask)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![UI/UX](https://img.shields.io/badge/UI--UX-Modern%20Design%20System-purple)](https://bootstrapget.com)

**DocManager** is a full-featured, commercial-grade clinic management web application engineered for medical practitioners, doctors, and clinics. Built with Python (Flask) and a modern frontend design system, DocManager streamlines patient medical histories, clinical visit notes, prescription generation, appointment scheduling, billing, and practice analytics into a unified dashboard.

---

## ✨ Features at a Glance

### 1. 📊 Actionable Doctor Dashboard
- **Dynamic Welcome Hero**: Time-aware greetings (*Good Morning / Afternoon / Evening*), live clock, doctor avatar, and clinic status.
- **Real-Time KPI Cards**: Total Patients (with trend indicators `▲ +12% this week`), Today's Visits, Today's Appointments, and Follow-ups Due.
- **Actionable Schedule Timeline**: Interactive timeline of today's appointments with instant completion status toggles.
- **Overdue Follow-up Alerts**: Automatic tracking of overdue patient reviews with direct phone call triggers.

### 2. 👤 Comprehensive Patient Profile Hub
- **Tabbed Patient Hub**:
  - **Overview**: Vitals, blood group badge, age/gender, address, and emergency contact details.
  - **Medical Timeline**: Visual vertical timeline tracking past diagnoses, prescriptions, lab reports, and follow-ups.
  - **Prescriptions**: List of prescriptions with one-click ReportLab PDF exports.
  - **Documents & Lab Reports**: Drag-and-drop uploader for MRIs, X-Rays, Blood Reports with inline modal previews.
  - **Visits History**: Full clinical history table.
  - **Billing & Invoices**: Itemized bills, payment status badges, and Invoice PDF receipts.

### 3. 💊 Structured Prescription Builder & ReportLab PDFs
- **Multi-Medicine Dynamic Array**: Add multiple medicines with dosage, frequency (*1-0-1*, *1-1-1*), duration, and specific instructions.
- **PDF Export**: Generates professional PDF prescriptions complete with clinic logo, doctor details, patient metadata, medicine table, and authorized signature block.

### 4. 🧾 Commercial Patient Bill & Receipt Generator
- **Itemized Invoice Builder**: Service breakdown for consultation fees, medicines, clinical tests/procedures, and discount calculation.
- **Payment Method Badges**: Cash, UPI, and Card tracking.
- **Instant Print & PDF**: Printable invoice view (`window.print()`) and downloadable PDF receipts matching official clinic formats.

### 5. 🔍 Smart Search & Command Palette (`Ctrl + K`)
- **VS Code-style Command Palette (`Ctrl + K`)**: Instant search across patients, system navigation, and quick actions.
- **Multi-Filter Directory**: Search by Name, Mobile, Email, Patient ID, Gender, or Blood Group.

### 6. 📅 Appointment Scheduling
- Directory view with status filters (*Scheduled*, *Completed*, *Cancelled*).
- Easy booking form linked directly to patient profiles.

### 7. 📈 Interactive Analytics & Reports
- **Chart.js Dashboard**:
  - Weekly Patient Visits Trend Line Chart.
  - Patient Gender Demographics Doughnut Chart.
  - Daily Billing Revenue Bar Chart.
  - Top Diagnoses Distribution Bar Chart.

### 8. 🌙 Dark Mode & Responsive Mobile UI
- Persistent theme switching (**Light / Dark Mode**) saved in `localStorage`.
- Mobile-first bottom navigation bar and floating speed dial action button (**+ FAB**).

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, ReportLab
- **Database**: SQLite / PostgreSQL (SQLAlchemy ORM)
- **Frontend**: HTML5, Vanilla CSS Design System (CSS Custom Property Tokens), JavaScript (ES6+)
- **Styling**: Bootstrap 5.3, Bootstrap Icons 1.11, Google Fonts (*Inter* & *Outfit*)
- **Data Visualization**: Chart.js 4.4

---

## 📁 Project Architecture

```text
DocManager/
├── app/
│   ├── __init__.py          # Application Factory (create_app) & Auto DB Migration
│   └── blueprints/
│       ├── analytics.py     # Analytics & Reports API
│       ├── api.py           # Command Palette & Calendar REST API
│       ├── appointments.py  # Appointments scheduling & views
│       ├── auth.py          # Login, Register, Logout routes
│       ├── billing.py       # Billing & Invoice PDF Generator
│       ├── patients.py      # Patient directory, profile hub & uploads
│       ├── settings.py      # Doctor profile & clinic branding
│       └── visits.py        # Clinical visits & Prescription PDF Generator
├── instance/
│   └── docmanager.db        # SQLite Database
├── static/
│   ├── css/
│   │   └── style.css        # Full CSS Design System & Dark Mode
│   ├── documents/           # Uploaded lab reports & PDFs
│   ├── js/
│   │   └── app.js           # Command Palette, Dark Mode & Shortcuts
│   └── uploads/             # Clinic logos
├── templates/               # Jinja2 HTML Templates
├── .env.example             # Environment Configuration Template
├── .gitignore               # Git Ignore Rules
├── app.py                   # Main Application Entry Point
├── config.py                # Configuration Settings
├── models.py                # SQLAlchemy Models
└── requirements.txt         # Dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** installed.
- **Git** installed.

### 2. Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SM71234/DocManager.git
   cd DocManager
   ```

2. **Create and Activate Virtual Environment**:
   - **Windows**:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Linux/macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables** (Optional):
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///instance/docmanager.db
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```

6. **Access in Browser**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + K` / `Cmd + K` | Open Command Palette (Global Search) |
| `N` | Register New Patient |
| `/` | Focus Global Search |
| `Esc` | Close Modals & Command Palette |

---

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
