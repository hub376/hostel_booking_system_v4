import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

@app.route("/")
def home():
    hostels = query_db('SELECT * FROM hostels WHERE listing_status = "active" LIMIT 6')
    return render_template('index.html', hostels=hostels)

# Student routes
@app.route("/student/register", methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        university = request.form['university']
        
        try:
            insert_db('INSERT INTO students (name, email, password, phone, university) VALUES (?, ?, ?, ?, ?)',
                     [name, email, password, phone, university])
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
    
    return render_template('student_register.html')

@app.route("/student/login", methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = query_db('SELECT * FROM students WHERE email = ?', [email], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_type'] = 'student'
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'error')
    
    return render_template('student_login.html')

@app.route("/student/logout")
def student_logout():
    session.clear()
    return redirect(url_for('home'))

# Hostel admin routes
@app.route("/hostel-admin/register", methods=['GET', 'POST'])
def hostel_admin_register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        
        try:
            insert_db('INSERT INTO hostel_admins (full_name, email, password, phone) VALUES (?, ?, ?, ?)',
                     [full_name, email, password, phone])
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('hostel_admin_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
    
    return render_template('hostel_admin_register.html')

@app.route("/hostel-admin/login", methods=['GET', 'POST'])
def hostel_admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = query_db('SELECT * FROM hostel_admins WHERE email = ?', [email], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_type'] = 'hostel_admin'
            return redirect(url_for('hostel_admin_dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    
    return render_template('hostel_admin_login.html')

@app.route("/hostel-admin/logout")
def hostel_admin_logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/hostel-admin/dashboard")
def hostel_admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'hostel_admin':
        return redirect(url_for('hostel_admin_login'))
    
    hostels = query_db('SELECT * FROM hostels WHERE hostel_admin_id = ?', [session['user_id']])
    return render_template('hostel_admin_dashboard.html', hostels=hostels)

# Admin routes
@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = query_db('SELECT * FROM super_admins WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_type'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    
    return render_template('admin_login.html')

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/admin/dashboard")
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    # Get stats
    total_students = query_db('SELECT COUNT(*) as count FROM students', one=True)['count']
    total_hostels = query_db('SELECT COUNT(*) as count FROM hostels', one=True)['count']
    total_bookings = query_db('SELECT COUNT(*) as count FROM bookings', one=True)['count']
    pending_payments = query_db('SELECT COUNT(*) as count FROM payments WHERE verification_status = "pending"', one=True)['count']
    
    return render_template('admin_dashboard.html', 
                         total_students=total_students,
                         total_hostels=total_hostels,
                         total_bookings=total_bookings,
                         pending_payments=pending_payments)

# Hostel listing
@app.route("/hostels")
def hostels():
    hostels = query_db('SELECT * FROM hostels WHERE listing_status = "active"')
    return render_template('hostel.html', hostels=hostels)

@app.route("/hostel/<int:hostel_id>")
def hostel_detail(hostel_id):
    hostel = query_db('SELECT * FROM hostels WHERE id = ?', [hostel_id], one=True)
    if not hostel:
        flash('Hostel not found.', 'error')
        return redirect(url_for('hostels'))
    
    reviews = query_db('SELECT r.*, s.name FROM reviews r JOIN students s ON r.student_id = s.id WHERE r.hostel_id = ?', [hostel_id])
    avg_rating = query_db('SELECT AVG(rating) as avg FROM reviews WHERE hostel_id = ?', [hostel_id], one=True)['avg'] or 0
    
    return render_template('hostel_detail.html', hostel=hostel, reviews=reviews, avg_rating=round(avg_rating, 1))

# Booking
@app.route("/booking/<int:hostel_id>", methods=['GET', 'POST'])
def booking(hostel_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    hostel = query_db('SELECT * FROM hostels WHERE id = ?', [hostel_id], one=True)
    if not hostel:
        flash('Hostel not found.', 'error')
        return redirect(url_for('hostels'))
    
    if request.method == 'POST':
        insert_db('INSERT INTO bookings (student_id, hostel_id) VALUES (?, ?)', [session['user_id'], hostel_id])
        flash('Booking request submitted!', 'success')
        return redirect(url_for('my_bookings'))
    
    return render_template('booking.html', hostel=hostel)

@app.route("/my-bookings")
def my_bookings():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    bookings = query_db('''
        SELECT b.*, h.name, h.location, h.price 
        FROM bookings b 
        JOIN hostels h ON b.hostel_id = h.id 
        WHERE b.student_id = ?
    ''', [session['user_id']])
    
    return render_template('my_booking.html', bookings=bookings)

# Reviews
@app.route("/review/<int:hostel_id>", methods=['GET', 'POST'])
def review(hostel_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    hostel = query_db('SELECT * FROM hostels WHERE id = ?', [hostel_id], one=True)
    if not hostel:
        flash('Hostel not found.', 'error')
        return redirect(url_for('hostels'))
    
    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form['comment']
        insert_db('INSERT INTO reviews (student_id, hostel_id, rating, comment) VALUES (?, ?, ?, ?)',
                 [session['user_id'], hostel_id, rating, comment])
        flash('Review submitted!', 'success')
        return redirect(url_for('hostel_detail', hostel_id=hostel_id))
    
    return render_template('review_form.html', hostel=hostel)

# Add hostel
@app.route("/hostel-admin/add-hostel", methods=['GET', 'POST'])
def add_hostel():
    if 'user_type' not in session or session['user_type'] != 'hostel_admin':
        return redirect(url_for('hostel_admin_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        price = request.form['price']
        seats = request.form['seats']
        room_type = request.form['room_type']
        distance_km = request.form['distance_km']
        description = request.form['description']
        map_link = request.form['map_link']
        
        # Handle file upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = filename
        
        insert_db('''
            INSERT INTO hostels (hostel_admin_id, name, location, price, seats, room_type, distance_km, description, image_url, map_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [session['user_id'], name, location, price, seats, room_type, distance_km, description, image_url, map_link])
        
        flash('Hostel added successfully!', 'success')
        return redirect(url_for('hostel_admin_dashboard'))
    
    return render_template('add_hostel.html')

# Payment
@app.route("/hostel-admin/payment/<int:hostel_id>", methods=['GET', 'POST'])
def payment(hostel_id):
    if 'user_type' not in session or session['user_type'] != 'hostel_admin':
        return redirect(url_for('hostel_admin_login'))
    
    hostel = query_db('SELECT * FROM hostels WHERE id = ? AND hostel_admin_id = ?', [hostel_id, session['user_id']], one=True)
    if not hostel:
        flash('Hostel not found.', 'error')
        return redirect(url_for('hostel_admin_dashboard'))
    
    if request.method == 'POST':
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        transaction_ref = request.form['transaction_ref']
        screenshot_note = request.form['screenshot_note']
        
        insert_db('''
            INSERT INTO payments (hostel_id, hostel_admin_id, amount, payment_method, transaction_ref, screenshot_note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [hostel_id, session['user_id'], amount, payment_method, transaction_ref, screenshot_note])
        
        flash('Payment submitted for verification!', 'success')
        return redirect(url_for('hostel_admin_dashboard'))
    
    return render_template('payment_page.html', hostel=hostel)

# Admin manage bookings
@app.route("/admin/manage-bookings")
def manage_bookings():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    bookings = query_db('''
        SELECT b.*, h.name as hostel_name, s.name as student_name, s.email as student_email
        FROM bookings b
        JOIN hostels h ON b.hostel_id = h.id
        JOIN students s ON b.student_id = s.id
    ''')
    
    return render_template('manage_booking.html', bookings=bookings)

# Admin manage payments
@app.route("/admin/manage-payments")
def manage_payments():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    payments = query_db('''
        SELECT p.*, h.name as hostel_name, ha.full_name as admin_name
        FROM payments p
        JOIN hostels h ON p.hostel_id = h.id
        JOIN hostel_admins ha ON p.hostel_admin_id = ha.id
    ''')
    
    return render_template('manage_payments.html', payments=payments)

@app.route("/admin/payment/<int:payment_id>/approve", methods=['POST'])
def approve_payment(payment_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    insert_db('UPDATE payments SET verification_status = "approved" WHERE id = ?', [payment_id])
    insert_db('UPDATE hostels SET payment_status = "paid", listing_status = "active" WHERE id = (SELECT hostel_id FROM payments WHERE id = ?)', [payment_id])
    flash('Payment approved!', 'success')
    return redirect(url_for('manage_payments'))

@app.route("/admin/payment/<int:payment_id>/reject", methods=['POST'])
def reject_payment(payment_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    insert_db('UPDATE payments SET verification_status = "rejected" WHERE id = ?', [payment_id])
    flash('Payment rejected!', 'error')
    return redirect(url_for('manage_payments'))

# Admin manage reviews
@app.route("/admin/manage-reviews")
def manage_reviews():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    reviews = query_db('''
        SELECT r.*, h.name as hostel_name, s.name as student_name
        FROM reviews r
        JOIN hostels h ON r.hostel_id = h.id
        JOIN students s ON r.student_id = s.id
    ''')
    
    return render_template('manage_reviews.html', reviews=reviews)

@app.route("/admin/review/<int:review_id>/delete", methods=['POST'])
def delete_review(review_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    insert_db('DELETE FROM reviews WHERE id = ?', [review_id])
    flash('Review deleted!', 'success')
    return redirect(url_for('manage_reviews'))

# Reports
@app.route("/admin/reports")
def reports():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    # Sample report data
    report_data = {
        'total_hostels': query_db('SELECT COUNT(*) as count FROM hostels', one=True)['count'],
        'active_hostels': query_db('SELECT COUNT(*) as count FROM hostels WHERE listing_status = "active"', one=True)['count'],
        'total_bookings': query_db('SELECT COUNT(*) as count FROM bookings', one=True)['count'],
        'pending_bookings': query_db('SELECT COUNT(*) as count FROM bookings WHERE status = "pending"', one=True)['count'],
        'total_payments': query_db('SELECT SUM(amount) as total FROM payments WHERE verification_status = "approved"', one=True)['total'] or 0,
    }
    
    return render_template('report_page.html', **report_data)

# Student profile
@app.route("/student/profile", methods=['GET', 'POST'])
def student_profile():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        university = request.form['university']
        
        insert_db('UPDATE students SET name = ?, phone = ?, university = ? WHERE id = ?',
                 [name, phone, university, session['user_id']])
        flash('Profile updated!', 'success')
        return redirect(url_for('student_profile'))
    
    user = query_db('SELECT * FROM students WHERE id = ?', [session['user_id']], one=True)
    return render_template('student_profile.html', user=user)

# Recommendations (simple implementation)
@app.route("/recommend")
def recommend():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    # Simple recommendation: hostels not booked by the student
    booked_hostels = query_db('SELECT hostel_id FROM bookings WHERE student_id = ?', [session['user_id']])
    booked_ids = [b['hostel_id'] for b in booked_hostels]
    
    if booked_ids:
        placeholders = ','.join('?' * len(booked_ids))
        recommended = query_db(f'SELECT * FROM hostels WHERE listing_status = "active" AND id NOT IN ({placeholders})', booked_ids)
    else:
        recommended = query_db('SELECT * FROM hostels WHERE listing_status = "active"')
    
    return render_template('recommend.html', hostels=recommended)

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
