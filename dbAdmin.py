from cs50 import SQL
from datetime import datetime

# Connect to DB
db = SQL("sqlite:///info.db")
data = db.execute("SELECT users.name, users.email, events.price, tickets.created_at FROM tickets JOIN events ON tickets.event_id = events.id JOIN users ON tickets.user_id = users.id WHERE events.id = ?", 1)
print(data)