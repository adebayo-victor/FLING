import os
from cs50 import SQL
from datetime import datetime
from google.cloud import storage
from dotenv import load_dotenv
#start virtual environment
load_dotenv()
# Make sure you are using an environment variable for security on Render
# Replace this line with your Render DATABASE_URL environment variable
db = SQL(os.environ.get("DATABASE_URL"))

try:
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


except Exception as e:
    # A general try-except block to catch any database-related errors
    print(f"❌ An error occurred during database setup: {e}")