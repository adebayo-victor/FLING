from cs50 import SQL
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
# Connect to DB
db = SQL("sqlite:///info.db")

# --- TABLE CREATION ---

# USERS TABLE (Updated with `img` column)
db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL,
        bank_name VARCHAR(255) NOT NULL,
        bank_code VARCHAR(50) NOT NULL,
        account_number VARCHAR(20) NOT NULL,
        account_name VARCHAR(255) NOT NULL,
        subaccount_code VARCHAR(100) NOT NULL,
        img TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# EVENTS TABLE (Updated to accommodate three pictures and one video path)
db.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        location TEXT,
        date DATE NOT NULL,
        time TIME NOT NULL,
        price INTEGER NOT NULL,
        url_key VARCHAR UNIQUE,
        html TEXT,
        img1 TEXT,
        img2 TEXT,
        img3 TEXT,
        video TEXT,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )
""")

# TICKETS TABLE
db.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        ticket_code TEXT UNIQUE NOT NULL,
        qr_code TEXT,
        status TEXT DEFAULT 'valid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(event_id) REFERENCES events(id)
    )
""")

# PAYMENT TABLE (optional)
db.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        reference TEXT UNIQUE NOT NULL,
        payment_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(event_id) REFERENCES events(id)
    )
""")

print("✅ All tables created with updated events table.")