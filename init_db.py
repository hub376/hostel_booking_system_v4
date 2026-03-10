import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT,
    university TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS super_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hostel_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hostels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_admin_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    price INTEGER NOT NULL,
    seats INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    distance_km REAL DEFAULT 0,
    description TEXT,
    image_url TEXT,
    map_link TEXT,
    listing_status TEXT DEFAULT 'inactive',
    payment_status TEXT DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(hostel_admin_id) REFERENCES hostel_admins(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(hostel_id) REFERENCES hostels(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_id INTEGER NOT NULL,
    hostel_admin_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    transaction_ref TEXT,
    screenshot_note TEXT,
    verification_status TEXT DEFAULT 'pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(hostel_id) REFERENCES hostels(id),
    FOREIGN KEY(hostel_admin_id) REFERENCES hostel_admins(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(hostel_id) REFERENCES hostels(id)
)
""")

cursor.execute("SELECT COUNT(*) FROM super_admins")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO super_admins (username, password)
        VALUES (?, ?)
    """, ("admin", generate_password_hash("admin123")))

cursor.execute("SELECT COUNT(*) FROM hostel_admins WHERE email = ?", ("owner@example.com",))
exists = cursor.fetchone()[0]
if exists == 0:
    cursor.execute("""
        INSERT INTO hostel_admins (full_name, email, password, phone)
        VALUES (?, ?, ?, ?)
    """, ("Demo Owner", "owner@example.com", generate_password_hash("owner123"), "03001234567"))

cursor.execute("SELECT id FROM hostel_admins WHERE email = ?", ("owner@example.com",))
owner_id = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM hostels")
if cursor.fetchone()[0] == 0:
    sample_hostels = [
        (owner_id, "City Hostel", "Peshawar", 5000, 10, "Single", 2.5, "Clean rooms near university", "", "https://maps.google.com", "active", "paid"),
        (owner_id, "Peace Hostel", "Hayatabad", 6500, 8, "Double", 4.0, "Peaceful and secure environment", "", "https://maps.google.com", "active", "paid"),
        (owner_id, "Student Point", "University Road", 4500, 12, "Shared", 1.5, "Affordable hostel for students", "", "https://maps.google.com", "active", "paid")
    ]

    cursor.executemany("""
        INSERT INTO hostels (
            hostel_admin_id, name, location, price, seats, room_type,
            distance_km, description, image_url, map_link, listing_status, payment_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_hostels)

conn.commit()
conn.close()

print("Database initialized successfully.")
print("Admin login: admin / admin123")
print("Demo hostel owner: owner@example.com / owner123")