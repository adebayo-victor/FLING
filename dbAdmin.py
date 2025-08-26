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

# --- TABLE CREATION FOR POSTGRESQL ---

try:
    # USERS TABLE (Updated for Postgres)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password VARCHAR(255) NOT NULL,
            bank_name VARCHAR(255) NOT NULL,
            bank_code VARCHAR(50) NOT NULL,
            account_number VARCHAR(20) NOT NULL,
            account_name VARCHAR(255) NOT NULL,
            subaccount_code VARCHAR(100) NOT NULL,
            img TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # EVENTS TABLE (Updated for Postgres)
    db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            location TEXT,
            date DATE NOT NULL,
            time TIME NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            url_key VARCHAR(255) UNIQUE,
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

    # TICKETS TABLE (Updated for Postgres)
    db.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            ticket_code VARCHAR(255) UNIQUE NOT NULL,
            qr_code TEXT,
            status VARCHAR(50) DEFAULT 'valid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)

    # PAYMENT TABLE (Updated for Postgres)
    db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            reference VARCHAR(255) UNIQUE NOT NULL,
            payment_status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)
    print("✅ All tables created with updated events table.")

except Exception as e:
    print(f"Error creating tables: {e}")
