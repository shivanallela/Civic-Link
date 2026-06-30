# CivicLink — AI-Powered Civic Issue Reporter (Flask & SQLite Edition)

CivicLink is a full-stack, responsive web application for reporting and managing civic infrastructure issues. The platform allows citizens to submit complaints, earn reward points, and track repairs, while municipal authorities (Admins/City Employees) can assign departments, review reports, and update issues to completion with photographic proof.

This application is built entirely using:
- **Backend**: Python Flask
- **Database**: SQLite3
- **Frontend**: HTML5, Vanilla CSS, JS, Bootstrap 5, and Chart.js
- **No External API Dependencies**: Works completely locally.

---

## 🔐 Demo Accounts & Credentials

For quick evaluation, the database is auto-seeded on first run with the following credentials:

| Role | Email Address | Username (Shortcut) | Password |
|------|---------------|---------------------|----------|
| **Resident (Citizen)** | `alice@example.com` | `alice` | `user123` |
| **Resident (Citizen)** | `bob@example.com` | `bob` | `user123` |
| **City Employee (Admin)** | `emp01@civiclink.gov` | `emp01` | `emp123` |
| **City Employee (Admin)** | `emp02@civiclink.gov` | `emp02` | `emp123` |

*Note: You can log in using either the full email address or the username shortcut (e.g. `alice` / `emp01`).*

---

## 🔧 Installation & Local Setup

Follow these steps to run CivicLink on your machine:

### Step 1: Install Dependencies
Ensure you have Python 3.x installed. Navigate to the `CivicLink` directory and install the required libraries:
```bash
pip install -r requirements.txt
```

### Step 2: Launch the Flask Server
Run the Flask application:
```bash
python app.py
```
By default, the application will run at **http://localhost:5000**.

### Step 3: Access the Portal
Open your browser and navigate to:
- Home / Landing Page: `http://localhost:5000/`
- Register: `http://localhost:5000/register`
- Login: `http://localhost:5000/login`

---

## 📁 Folder Structure

```
CivicLink/
├── app.py                # Core Flask backend, routing, and SQLite DB configuration
├── requirements.txt      # Python dependencies (Flask)
├── README.md             # Installation Guide & User Manual (this file)
├── database/
│   └── civiclink.db      # Local SQLite database (auto-created on first run)
├── static/
│   ├── css/
│   │   └── style.css     # Premium government-style CSS and animations
│   ├── js/
│   │   └── app.js        # Client-side dynamic modal triggers & form validation
│   └── uploads/          # Saved complaint and resolution photos (auto-created)
└── templates/
    ├── base.html         # Common Jinja2 layout skeleton and navigation
    ├── index.html        # Public homepage showcasing recent resolved issues
    ├── login.html        # Authentication login screen
    ├── register.html     # Registration form for new Citizens/Employees
    ├── citizen_dashboard.html # Citizen stats, rewards points balance, and reports history
    ├── report_issue.html      # Civic issue reporting form with file previews
    ├── admin_dashboard.html   # Admin complaint console with filters and update modals
    └── analytics.html         # Dynamic analytical charts using Chart.js
```

---

## 📊 Database Schema Details

The application creates and manages two tables inside `database/civiclink.db`:

### 1. `users` Table
Stores registered citizens and city employees.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `name`: TEXT (Full Name)
- `email`: TEXT UNIQUE (Email Address)
- `password`: TEXT (Securely hashed using Werkzeug check/generate methods)
- `role`: TEXT (`citizen` or `admin`)
- `points`: INTEGER (Reward Points Balance, defaults to `0`)

### 2. `complaints` Table
Stores submitted civic issues and resolution records.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id`: INTEGER (FOREIGN KEY referencing `users.id`)
- `issue_type`: TEXT (Category: Pothole, Road Damage, Fallen Tree, Water Leakage, etc.)
- `description`: TEXT (Citizen description details)
- `location`: TEXT (Landmark/Street details)
- `severity`: TEXT (`Low`, `Medium`, `High`, `Critical`)
- `image_path`: TEXT (Relative path to the uploaded issue image file)
- `status`: TEXT (Status: `Pending`, `Assigned`, `In Progress`, `Resolved`)
- `resolution_image`: TEXT (Relative path to the uploaded resolution proof image file)
- `assigned_department`: TEXT (`Road Department`, `Water Department`, etc.)
- `created_at`: DATETIME (Timestamp of submission, defaults to CURRENT_TIMESTAMP)

---

## 🌟 Key Features Walkthrough

1. **Secure Authentication**: Uses industry-standard SHA256 password hashing. Sessions persist across browser visits.
2. **Citizen Reward Program**: Users receive **50 points** each time a complaint they submitted is verified and resolved by city employees.
3. **Automatic Routing**: Submission categories are automatically pre-mapped to corresponding city divisions:
   - *Pothole, Road Damage, Fallen Tree* &rarr; **Road Department**
   - *Water Leakage* &rarr; **Water Department**
   - *Broken Street Light, Property Damage* &rarr; **Electrical Department**
   - *Garbage Dump, Drainage Blockage* &rarr; **Sanitation Department**
4. **Before and After Image Side-by-Side**: Resolved complaints display both the before-repair photo and the after-repair proof side by side in the user interface.
5. **Interactive Analytics**: Displays four dynamic charts summarizing reporting volume by type, severity levels, monthly trends, and resolution rates.
