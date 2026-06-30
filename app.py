import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'civiclink_secret_key_change_me_in_production'

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'database', 'civiclink.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

# Ensure database and upload directories exist
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    ''')
    
    # Create Complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            issue_type TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            severity TEXT NOT NULL,
            image_path TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            resolution_image TEXT,
            assigned_department TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Seed demo users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("Alice", "alice@example.com", generate_password_hash("user123"), "citizen"),
            ("Bob", "bob@example.com", generate_password_hash("user123"), "citizen"),
            ("Employee 1", "emp01@civiclink.gov", generate_password_hash("emp123"), "admin"),
            ("Employee 2", "emp02@civiclink.gov", generate_password_hash("emp123"), "admin")
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            demo_users
        )
        conn.commit()
        
    conn.close()


# Initialize database tables
init_db()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_department_by_issue(issue_type):
    # Dynamic Auto-assignment helper based on issue category
    mapping = {
        'Pothole': 'Road Department',
        'Road Damage': 'Road Department',
        'Fallen Tree': 'Road Department',
        'Water Leakage': 'Water Department',
        'Broken Street Light': 'Electrical Department',
        'Public Property Damage': 'Electrical Department',
        'Garbage Dump': 'Sanitation Department',
        'Drainage Blockage': 'Sanitation Department'
    }
    return mapping.get(issue_type, 'Sanitation Department')


# --- AUTHENTICATION FILTERS ---
@app.before_request
def check_user_session():
    # Helper to load current user object if logged in
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        if user:
            session['user_points'] = user['points']
            session['user_name'] = user['name']
        else:
            session.clear()


# --- GENERAL ROUTES ---
@app.route('/')
def index():
    # Get a list of recently resolved complaints to display on landing page
    conn = get_db_connection()
    resolved_complaints = conn.execute('''
        SELECT c.*, u.name as citizen_name 
        FROM complaints c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.status = 'Resolved' 
        ORDER BY c.created_at DESC LIMIT 3
    ''').fetchall()
    conn.close()
    return render_template('index.html', resolved_complaints=resolved_complaints)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('citizen_dashboard' if session['role'] == 'citizen' else 'admin_dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'citizen')  # Default role is citizen
        
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, hashed_password, role)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An account with this email already exists.', 'danger')
        finally:
            conn.close()
            
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('citizen_dashboard' if session['role'] == 'citizen' else 'admin_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter email and password.', 'warning')
            return redirect(url_for('login'))
            
        # Support either exact email match OR seed usernames (alice, bob, emp01, emp02)
        conn = get_db_connection()
        user = None
        if '@' not in email:
            # Map simple usernames to their demo emails
            username_mapping = {
                'alice': 'alice@example.com',
                'bob': 'bob@example.com',
                'emp01': 'emp01@civiclink.gov',
                'emp02': 'emp02@civiclink.gov'
            }
            mapped_email = username_mapping.get(email.lower())
            if mapped_email:
                user = conn.execute("SELECT * FROM users WHERE email = ?", (mapped_email,)).fetchone()
        else:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['user_name'] = user['name']
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('citizen_dashboard'))
        else:
            flash('Invalid email/username or password.', 'danger')
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


# --- CITIZEN ROUTES ---
@app.route('/citizen/dashboard')
def citizen_dashboard():
    if 'user_id' not in session or session['role'] != 'citizen':
        flash('Access unauthorized. Please login as citizen.', 'danger')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    complaints = conn.execute('''
        SELECT * FROM complaints 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    # Calculate stats
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(case when status='Pending' then 1 else 0 end) as pending,
            SUM(case when status='In Progress' or status='Assigned' then 1 else 0 end) as active,
            SUM(case when status='Resolved' then 1 else 0 end) as resolved
        FROM complaints 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    conn.close()
    return render_template('citizen_dashboard.html', complaints=complaints, stats=stats)


@app.route('/citizen/report', methods=['GET', 'POST'])
def report_issue():
    if 'user_id' not in session or session['role'] != 'citizen':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        issue_type = request.form.get('issue_type')
        description = request.form.get('description')
        location = request.form.get('location')
        severity = request.form.get('severity')
        
        if not issue_type or not location or not severity:
            flash('Required fields: Issue Type, Location, Severity.', 'danger')
            return redirect(url_for('report_issue'))
            
        # Image handle
        file = request.files.get('image')
        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"uploads/{filename}"
            
        assigned_dept = get_department_by_issue(issue_type)
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO complaints (user_id, issue_type, description, location, severity, image_path, assigned_department, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (session['user_id'], issue_type, description, location, severity, image_path, assigned_dept))
        conn.commit()
        conn.close()
        
        flash('Issue reported successfully. You will receive reward points upon resolution!', 'success')
        return redirect(url_for('citizen_dashboard'))
        
    return render_template('report_issue.html')


# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access unauthorized. Employees only.', 'danger')
        return redirect(url_for('login'))
        
    # Search and Filter criteria
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    severity_filter = request.args.get('severity', '').strip()
    
    conn = get_db_connection()
    
    # Cards Info
    cards = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(case when status='Pending' then 1 else 0 end) as pending,
            SUM(case when status='In Progress' or status='Assigned' then 1 else 0 end) as active,
            SUM(case when status='Resolved' then 1 else 0 end) as resolved,
            SUM(case when severity='Critical' and status != 'Resolved' then 1 else 0 end) as critical
        FROM complaints
    ''').fetchone()
    
    # Build complaints query
    query = '''
        SELECT c.*, u.name as citizen_name, u.email as citizen_email 
        FROM complaints c 
        JOIN users u ON c.user_id = u.id 
        WHERE 1=1
    '''
    params = []
    
    if search_query:
        query += " AND (c.id LIKE ? OR c.description LIKE ? OR c.location LIKE ? OR u.name LIKE ?)"
        like_expr = f"%{search_query}%"
        params.extend([like_expr, like_expr, like_expr, like_expr])
        
    if status_filter:
        query += " AND c.status = ?"
        params.append(status_filter)
        
    if severity_filter:
        query += " AND c.severity = ?"
        params.append(severity_filter)
        
    query += " ORDER BY c.created_at DESC"
    complaints = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           complaints=complaints, 
                           cards=cards,
                           search=search_query,
                           status_filter=status_filter,
                           severity_filter=severity_filter)


@app.route('/admin/update-complaint/<int:complaint_id>', methods=['POST'])
def update_complaint(complaint_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    status = request.form.get('status')
    department = request.form.get('assigned_department')
    
    if not status:
        flash('Status is required for update.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    complaint = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    if not complaint:
        conn.close()
        flash('Complaint not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    resolution_image_path = complaint['resolution_image']
    
    # Handle resolution image upload
    file = request.files.get('resolution_image')
    if file and allowed_file(file.filename):
        filename = secure_filename(f"res_{int(datetime.now().timestamp())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        resolution_image_path = f"uploads/{filename}"
        
    # Validation rules: cannot resolve without resolution image
    if status == 'Resolved' and not resolution_image_path:
        conn.close()
        flash('A resolution image is required to mark a complaint as Resolved.', 'warning')
        return redirect(url_for('admin_dashboard'))
        
    # Update SQLite database
    conn.execute('''
        UPDATE complaints 
        SET status = ?, assigned_department = ?, resolution_image = ?
        WHERE id = ?
    ''', (status, department, resolution_image_path, complaint_id))
    
    # If transitioning to Resolved, award points to the citizen (Citizen Reward System: +50 points)
    if status == 'Resolved' and complaint['status'] != 'Resolved':
        conn.execute('UPDATE users SET points = points + 50 WHERE id = ?', (complaint['user_id'],))
        flash(f'Complaint #{complaint_id} updated to Resolved. Citizen awarded +50 points!', 'success')
    else:
        flash(f'Complaint #{complaint_id} updated successfully.', 'success')
        
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))


# --- ANALYTICS ROUTE ---
@app.route('/admin/analytics')
def analytics():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    # Query 1: Complaints by Issue Type
    by_type = conn.execute('''
        SELECT issue_type, COUNT(*) as count 
        FROM complaints 
        GROUP BY issue_type
    ''').fetchall()
    
    # Query 2: Complaints by Severity
    by_severity = conn.execute('''
        SELECT severity, COUNT(*) as count 
        FROM complaints 
        GROUP BY severity
    ''').fetchall()
    
    # Query 3: Monthly Complaints (for last 6 months)
    # SQLite strftime format %m or %Y-%m
    by_month = conn.execute('''
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
        FROM complaints 
        GROUP BY month 
        ORDER BY month ASC LIMIT 6
    ''').fetchall()
    
    # Query 4: Total & Resolved Count for Resolution Percentage
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(case when status='Resolved' then 1 else 0 end) as resolved
        FROM complaints
    ''').fetchone()
    
    # Query 5: Resolution rate per Department
    dept_resolution = conn.execute('''
        SELECT 
            assigned_department as dept,
            COUNT(*) as total,
            SUM(case when status='Resolved' then 1 else 0 end) as resolved
        FROM complaints 
        WHERE assigned_department IS NOT NULL
        GROUP BY assigned_department
    ''').fetchall()
    
    conn.close()
    
    # Prepare JSON data for Chart.js
    issue_type_labels = [row['issue_type'] for row in by_type]
    issue_type_data = [row['count'] for row in by_type]
    
    severity_labels = [row['severity'] for row in by_severity]
    severity_data = [row['count'] for row in by_severity]
    
    month_labels = [row['month'] for row in by_month]
    month_data = [row['count'] for row in by_month]
    
    dept_labels = [row['dept'] for row in dept_resolution]
    dept_totals = [row['total'] for row in dept_resolution]
    dept_resolved = [row['resolved'] for row in dept_resolution]
    dept_rates = [round((row['resolved'] / row['total']) * 100, 1) if row['total'] > 0 else 0 for row in dept_resolution]
    
    # Calculations for General Metrics
    total_count = stats['total'] if stats else 0
    resolved_count = stats['resolved'] if stats else 0
    resolution_rate = round((resolved_count / total_count) * 100, 1) if total_count > 0 else 0
    
    analytics_data = {
        'issue_type': {'labels': issue_type_labels, 'data': issue_type_data},
        'severity': {'labels': severity_labels, 'data': severity_data},
        'monthly': {'labels': month_labels, 'data': month_data},
        'department': {'labels': dept_labels, 'totals': dept_totals, 'resolved': dept_resolved, 'rates': dept_rates},
        'resolution_rate': resolution_rate,
        'total': total_count,
        'resolved': resolved_count
    }
    
    return render_template('analytics.html', data=analytics_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
