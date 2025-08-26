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
    print(db.execute("SELECT * FROM events")[0]['html'])
except Exception as e:
    print(f"❌ An error occurred during database setup: {e}")