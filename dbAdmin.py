from cs50 import SQL
from datetime import datetime

# Connect to DB
db = SQL("sqlite:///info.db")

# --- TABLE CREATION ---

print(db.execute("SELECT * FROM events"))