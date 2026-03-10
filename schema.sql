CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT,
    university TEXT
);

CREATE TABLE IF NOT EXISTS super_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hostel_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT
);

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
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(hostel_id) REFERENCES hostels(id)
);

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
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(hostel_id) REFERENCES hostels(id)
);