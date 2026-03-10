import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# Database connection
def get_db():
    conn = sqlite3.connect('database.db')
    return conn

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database if needed
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        email TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS hostels (
        id INTEGER PRIMARY KEY,
        name TEXT,
        location TEXT,
        price INTEGER,
        seats INTEGER,
        room_type TEXT,
        distance_km REAL,
        description TEXT,
        listing_status TEXT DEFAULT 'active',
        admin_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        hostel_id INTEGER,
        status TEXT DEFAULT 'pending',
        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        hostel_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Insert default users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ("admin", hash_password("admin123"), "admin", "admin@hostelhub.com"),
            ("student1", hash_password("student123"), "student", "student1@university.com"),
            ("owner1", hash_password("owner123"), "hostel_admin", "owner1@hostels.com")
        ]
        cursor.executemany("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)", default_users)

    # Insert sample hostels if empty
    cursor.execute("SELECT COUNT(*) FROM hostels")
    if cursor.fetchone()[0] == 0:
        sample_hostels = [
            ("City Hostel", "Peshawar", 5000, 10, "Single", 2.5, "Clean rooms near university", "active", 3),
            ("Peace Hostel", "Hayatabad", 6500, 8, "Double", 4.0, "Peaceful and secure environment", "active", 3),
            ("Student Point", "University Road", 4500, 12, "Shared", 1.5, "Affordable hostel for students", "active", 3)
        ]
        cursor.executemany("INSERT INTO hostels (name, location, price, seats, room_type, distance_km, description, listing_status, admin_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_hostels)

    conn.commit()
    conn.close()

# Authentication functions
def login_user(username, password):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and user[2] == hash_password(password):
        return {
            'id': user[0],
            'username': user[1],
            'role': user[3],
            'email': user[4]
        }
    return None

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# Check authentication
def check_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    return st.session_state.logged_in

# Streamlit app
st.set_page_config(page_title="HostelHub - Booking System", page_icon="🏠", layout="wide")

# Initialize database
init_db()

# Authentication check
if not check_auth():
    st.title("🔐 Login to HostelHub")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["student", "hostel_admin"])
            submitted = st.form_submit_button("Register")

            if submitted:
                try:
                    conn = get_db()
                    conn.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                               (new_username, hash_password(new_password), role, new_email))
                    conn.commit()
                    conn.close()
                    st.success("Registration successful! Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists")

    st.markdown("---")
    st.markdown("**Demo Credentials:**")
    st.code("Admin: admin / admin123\nStudent: student1 / student123\nHostel Owner: owner1 / owner123")

    st.stop()

# Main app - User is logged in
user = st.session_state.user

# Sidebar navigation
st.sidebar.title(f"🏠 HostelHub - {user['role'].title()}")
st.sidebar.markdown(f"**Welcome, {user['username']}!**")

# Role-based navigation
if user['role'] == 'admin':
    pages = ["Dashboard", "Manage Hostels", "Manage Bookings", "Manage Reviews", "Analytics"]
elif user['role'] == 'hostel_admin':
    pages = ["Dashboard", "My Hostels", "Add Hostel", "Manage Payments", "Bookings"]
else:  # student
    pages = ["Browse Hostels", "My Bookings", "My Reviews", "Recommendations"]

page = st.sidebar.radio("Navigate", pages)

if st.sidebar.button("Logout"):
    logout_user()

# Admin Dashboard
if page == "Dashboard" and user['role'] == 'admin':
    st.title("📊 Admin Dashboard")

    conn = get_db()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        st.metric("Total Users", total_users)

    with col2:
        total_hostels = conn.execute("SELECT COUNT(*) FROM hostels").fetchone()[0]
        st.metric("Total Hostels", total_hostels)

    with col3:
        total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        st.metric("Total Bookings", total_bookings)

    with col4:
        pending_payments = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'pending'").fetchone()[0]
        st.metric("Pending Bookings", pending_payments)

    conn.close()

# Student Browse Hostels
elif page == "Browse Hostels" and user['role'] == 'student':
    st.title("🏠 Available Hostels")

    conn = get_db()
    hostels = pd.read_sql_query("SELECT * FROM hostels WHERE listing_status = 'active'", conn)
    conn.close()

    if len(hostels) == 0:
        st.info("No hostels available at the moment.")
    else:
        for _, hostel in hostels.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image("https://via.placeholder.com/300x200?text=Hostel+Image", use_column_width=True)
                with col2:
                    st.subheader(f"{hostel['name']}")
                    st.write(f"📍 {hostel['location']}")
                    st.write(f"💰 Rs. {hostel['price']}/month")
                    st.write(f"🛏️ {hostel['room_type']} • {hostel['seats']} seats available")
                    st.write(f"📏 {hostel['distance_km']} km from university")
                    st.write(f"📝 {hostel['description']}")

                    # Check if already booked
                    conn = get_db()
                    existing_booking = conn.execute("SELECT id FROM bookings WHERE user_id = ? AND hostel_id = ?",
                                                  (user['id'], hostel['id'])).fetchone()
                    conn.close()

                    if existing_booking:
                        st.info("Already booked this hostel")
                    else:
                        if st.button(f"Book Now - {hostel['name']}", key=f"book_{hostel['id']}"):
                            conn = get_db()
                            conn.execute("INSERT INTO bookings (user_id, hostel_id) VALUES (?, ?)",
                                       (user['id'], hostel['id']))
                            conn.commit()
                            conn.close()
                            st.success(f"Booking request submitted for {hostel['name']}!")
                            st.rerun()

                st.divider()

# Student My Bookings
elif page == "My Bookings" and user['role'] == 'student':
    st.title("📋 My Bookings")

    conn = get_db()
    bookings = pd.read_sql_query("""
        SELECT b.id, h.name, h.location, h.price, b.status, b.booking_date
        FROM bookings b
        JOIN hostels h ON b.hostel_id = h.id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    """, conn, params=(user['id'],))
    conn.close()

    if len(bookings) == 0:
        st.info("You haven't booked any hostels yet.")
    else:
        for _, booking in bookings.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🏠 **{booking['name']}** - {booking['location']}")
                    st.write(f"💰 Rs. {booking['price']}/month")
                    st.write(f"📅 Booked on: {booking['booking_date']}")
                with col2:
                    status_color = "🟡" if booking['status'] == 'pending' else "🟢"
                    st.write(f"{status_color} {booking['status'].title()}")

                    if booking['status'] == 'pending':
                        if st.button("Cancel", key=f"cancel_{booking['id']}"):
                            conn = get_db()
                            conn.execute("DELETE FROM bookings WHERE id = ?", (booking['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Booking cancelled!")
                            st.rerun()
                st.divider()

# Student Reviews
elif page == "My Reviews" and user['role'] == 'student':
    st.title("⭐ My Reviews")

    tab1, tab2 = st.tabs(["My Reviews", "Add Review"])

    with tab1:
        conn = get_db()
        reviews = pd.read_sql_query("""
            SELECT r.rating, r.comment, r.created_at, h.name as hostel_name
            FROM reviews r
            JOIN hostels h ON r.hostel_id = h.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        """, conn, params=(user['id'],))
        conn.close()

        if len(reviews) == 0:
            st.info("You haven't written any reviews yet.")
        else:
            for _, review in reviews.iterrows():
                with st.container():
                    st.write(f"🏠 **{review['hostel_name']}**")
                    st.write(f"⭐ Rating: {review['rating']}/5")
                    st.write(f"💬 {review['comment']}")
                    st.write(f"📅 {review['created_at']}")
                    st.divider()

    with tab2:
        conn = get_db()
        # Get hostels user has booked
        booked_hostels = pd.read_sql_query("""
            SELECT DISTINCT h.id, h.name
            FROM bookings b
            JOIN hostels h ON b.hostel_id = h.id
            WHERE b.user_id = ?
        """, conn, params=(user['id'],))
        conn.close()

        if len(booked_hostels) == 0:
            st.info("You need to book a hostel first before writing a review.")
        else:
            selected_hostel = st.selectbox("Select Hostel to Review",
                                         booked_hostels['name'].tolist())
            hostel_id = booked_hostels[booked_hostels['name'] == selected_hostel]['id'].iloc[0]

            # Check if already reviewed
            conn = get_db()
            existing_review = conn.execute("SELECT id FROM reviews WHERE user_id = ? AND hostel_id = ?",
                                         (user['id'], hostel_id)).fetchone()
            conn.close()

            if existing_review:
                st.info("You have already reviewed this hostel.")
            else:
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Your Review", height=100)

                if st.button("Submit Review"):
                    if comment.strip():
                        conn = get_db()
                        conn.execute("INSERT INTO reviews (user_id, hostel_id, rating, comment) VALUES (?, ?, ?, ?)",
                                   (user['id'], hostel_id, rating, comment))
                        conn.commit()
                        conn.close()
                        st.success("Review submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a review comment.")

# Hostel Admin Dashboard
elif page == "Dashboard" and user['role'] == 'hostel_admin':
    st.title("🏠 Hostel Admin Dashboard")

    conn = get_db()
    my_hostels = pd.read_sql_query("SELECT * FROM hostels WHERE admin_id = ?", conn, params=(user['id'],))
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings b JOIN hostels h ON b.hostel_id = h.id WHERE h.admin_id = ?",
                                (user['id'],)).fetchone()[0]
    conn.close()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("My Hostels", len(my_hostels))
    with col2:
        st.metric("Total Bookings", total_bookings)

# Hostel Admin My Hostels
elif page == "My Hostels" and user['role'] == 'hostel_admin':
    st.title("🏠 My Hostels")

    conn = get_db()
    hostels = pd.read_sql_query("SELECT * FROM hostels WHERE admin_id = ?", conn, params=(user['id'],))
    conn.close()

    if len(hostels) == 0:
        st.info("You haven't added any hostels yet.")
    else:
        for _, hostel in hostels.iterrows():
            with st.expander(f"{hostel['name']} - {hostel['location']}"):
                st.write(f"💰 Price: Rs. {hostel['price']}/month")
                st.write(f"🛏️ Type: {hostel['room_type']} • Seats: {hostel['seats']}")
                st.write(f"📏 Distance: {hostel['distance_km']} km")
                st.write(f"📝 {hostel['description']}")
                st.write(f"📊 Status: {hostel['listing_status']}")

# Hostel Admin Add Hostel
elif page == "Add Hostel" and user['role'] == 'hostel_admin':
    st.title("➕ Add New Hostel")

    with st.form("add_hostel_form"):
        name = st.text_input("Hostel Name")
        location = st.text_input("Location")
        price = st.number_input("Price per month", min_value=0)
        seats = st.number_input("Number of seats", min_value=1)
        room_type = st.selectbox("Room Type", ["Single", "Double", "Shared"])
        distance_km = st.number_input("Distance from university (km)", min_value=0.0)
        description = st.text_area("Description")

        submitted = st.form_submit_button("Add Hostel")

        if submitted:
            if name and location and description:
                conn = get_db()
                conn.execute("""
                    INSERT INTO hostels (name, location, price, seats, room_type, distance_km, description, admin_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, location, price, seats, room_type, distance_km, description, user['id']))
                conn.commit()
                conn.close()
                st.success("Hostel added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

# Admin Manage Hostels
elif page == "Manage Hostels" and user['role'] == 'admin':
    st.title("🏠 Manage All Hostels")

    conn = get_db()
    hostels = pd.read_sql_query("SELECT h.*, u.username as admin_name FROM hostels h JOIN users u ON h.admin_id = u.id", conn)
    conn.close()

    st.dataframe(hostels)

    # Edit hostel status
    st.subheader("Update Hostel Status")
    if len(hostels) > 0:
        selected_hostel = st.selectbox("Select Hostel", hostels['name'].tolist())
        hostel_id = hostels[hostels['name'] == selected_hostel]['id'].iloc[0]
        current_status = hostels[hostels['name'] == selected_hostel]['listing_status'].iloc[0]

        new_status = st.selectbox("New Status", ["active", "inactive"],
                                index=0 if current_status == "active" else 1)

        if st.button("Update Status"):
            conn = get_db()
            conn.execute("UPDATE hostels SET listing_status = ? WHERE id = ?", (new_status, hostel_id))
            conn.commit()
            conn.close()
            st.success("Hostel status updated!")
            st.rerun()

# Admin Manage Bookings
elif page == "Manage Bookings" and user['role'] == 'admin':
    st.title("📋 Manage Bookings")

    conn = get_db()
    bookings = pd.read_sql_query("""
        SELECT b.id, b.status, b.booking_date, h.name as hostel_name, u.username as student_name
        FROM bookings b
        JOIN hostels h ON b.hostel_id = h.id
        JOIN users u ON b.user_id = u.id
        ORDER BY b.booking_date DESC
    """, conn)
    conn.close()

    if len(bookings) == 0:
        st.info("No bookings found.")
    else:
        for _, booking in bookings.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"🏠 {booking['hostel_name']}")
                    st.write(f"👤 Student: {booking['student_name']}")
                    st.write(f"📅 {booking['booking_date']}")
                with col2:
                    status_color = "🟡" if booking['status'] == 'pending' else "🟢"
                    st.write(f"{status_color} {booking['status'].title()}")
                with col3:
                    if booking['status'] == 'pending':
                        col_approve, col_reject = st.columns(2)
                        with col_approve:
                            if st.button("✅ Approve", key=f"approve_{booking['id']}"):
                                conn = get_db()
                                conn.execute("UPDATE bookings SET status = 'confirmed' WHERE id = ?", (booking['id'],))
                                conn.commit()
                                conn.close()
                                st.success("Booking approved!")
                                st.rerun()
                        with col_reject:
                            if st.button("❌ Reject", key=f"reject_{booking['id']}"):
                                conn = get_db()
                                conn.execute("DELETE FROM bookings WHERE id = ?", (booking['id'],))
                                conn.commit()
                                conn.close()
                                st.success("Booking rejected!")
                                st.rerun()
                st.divider()

# Admin Analytics
elif page == "Analytics" and user['role'] == 'admin':
    st.title("📊 Analytics")

    conn = get_db()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Bookings by Hostel")
        booking_data = pd.read_sql_query("""
            SELECT h.name, COUNT(b.id) as bookings
            FROM hostels h
            LEFT JOIN bookings b ON h.id = b.hostel_id
            GROUP BY h.id, h.name
        """, conn)
        if len(booking_data) > 0:
            st.bar_chart(booking_data.set_index('name'))

    with col2:
        st.subheader("Average Ratings")
        rating_data = pd.read_sql_query("""
            SELECT h.name, AVG(r.rating) as avg_rating
            FROM hostels h
            LEFT JOIN reviews r ON h.id = r.hostel_id
            GROUP BY h.id, h.name
        """, conn)
        if len(rating_data) > 0:
            st.bar_chart(rating_data.set_index('name'))

    conn.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("HostelHub - Complete Booking System\nBuilt with Streamlit")
st.sidebar.markdown(f"**Logged in as:** {user['username']} ({user['role']})")