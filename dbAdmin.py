import os
from cs50 import SQL
from datetime import datetime
from google.cloud import storage
from dotenv import load_dotenv

# Start virtual environment
load_dotenv()

# Use your Render DATABASE_URL with ?sslmode=require for PostgreSQL
db = SQL(os.environ.get("DATABASE_URL"))

try:
    # USERS TABLE
    events = db.execute("SELECT * \
        FROM tickets JOIN users ON users.id = tickets.user_id \
        JOIN events ON events.id = tickets.event_id WHERE events.url_key = ?", "QERURF8SV")
    print(len(events))
except Exception as e:
    print(f"❌ An error occurred during database setup: {e}")