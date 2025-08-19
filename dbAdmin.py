from cs50 import SQL
from datetime import datetime

# Connect to DB
db = SQL("sqlite:///info.db")

# --- TABLE CREATION ---
format_string = "%Y-%m-%d %H:%M:%S"
date = db.execute("SELECT * FROM events")[0]['created_at']
datetime_object = datetime.strptime(date, format_string)
print(datetime_object)