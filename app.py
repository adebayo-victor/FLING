import random
import csv
import requests
from datetime import datetime, timedelta, date, time
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_file, make_response
import pandas as pd
from flask_cors import CORS
from cs50 import SQL
import secrets
import os
from werkzeug.utils import secure_filename
import string
import io
import xlsxwriter
from google.cloud import storage
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
#configuring for upload and download to cache
# Configure Cloudinary
cloudinary.config(
  cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key=os.environ.get('CLOUDINARY_API_KEY'),
  api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Cloudinary Upload Helper (updated to accept a custom filename)
def upload_file_to_cloudinary(file, folder_name=None, custom_filename=None):
    """
    Uploads a file to Cloudinary and returns the URL.
    Optionally organizes the upload into a specified folder and uses a custom filename.
    """
    try:
        # Save the file to a temporary path to be uploaded
        temp_path = os.path.join("/tmp", secure_filename(file.filename))
        file.save(temp_path)

        # Create a dictionary for upload parameters
        upload_params = {}

        # If a folder is specified, add it to the parameters
        if folder_name:
            upload_params['folder'] = folder_name

        # If a custom filename is specified, add it to the parameters.
        # Cloudinary will use this as the public_id.
        if custom_filename:
            # We remove the file extension from the custom filename to let Cloudinary handle it correctly.
            public_id = os.path.splitext(custom_filename)[0]
            upload_params['public_id'] = public_id

        # Upload the file from the temporary location with the specified parameters
        result = cloudinary.uploader.upload(temp_path, **upload_params)

        # Clean up the temporary file
        os.remove(temp_path)

        return result['url']
    except Exception as e:
        print(f"❌ Error uploading to Cloudinary: {e}")
        return None
#HTML file saving function, ahahahahahahahah, hell yeah
def save_html(html_content: str, file_name: str, folder_path: str):
    """
    Saves HTML content to a file.
    
    Args:
        html_content (str): The HTML content as a string.
        file_name (str): The file name (e.g., "index.html").
        folder_path (str): The folder path to save into.
    """
    try:
        # Ensure folder exists
        os.makedirs(folder_path, exist_ok=True)

        # Full file path
        file_path = os.path.join(folder_path, file_name)

        # Write the HTML content
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        print(f"✅ HTML file saved: {file_path}")

    except Exception as e:
        print(f"❌ Error saving HTML: {e}")

#loading virtual environment
load_dotenv()
#Initiating app ...
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("app_secret_key")
db = SQL(os.environ.get("DATABASE_URL"))
#gemini prompt functions
API_KEY = os.environ.get("gemini_key")
if not API_KEY:
    print("Error: Gemini API key not found. Please set 'gemini_key' in your .env file.")
    exit()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
#this function can also be used to generate other based on the prompt
def generate_ticket_template(prompt):
    """
    Sends a prompt to the Gemini API to request a full HTML template.
    """
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": API_KEY
    }
    
    # The payload is structured to ask the model for a text response
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=data, timeout=120)
        
        # Raise an exception for bad status codes
        response.raise_for_status()

        # Extract the HTML text from the response
        response_json = response.json()
        if 'candidates' in response_json and len(response_json['candidates']) > 0:
            html_template = response_json['candidates'][0]['content']['parts'][0]['text']
            return html_template
        else:
            print("Error: No candidates found in the response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Network or API Error: {e}")
        return None
def generate_url_code(length=9):
    characters = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(characters) for _ in range(length))
    return f"{random_part}"
def generate_code(length=6):
    characters = string.digits
    random_part = ''.join(secrets.choice(characters) for _ in range(length))
    return f"{random_part}"
#file upload functions
UPLOAD_FOLDER = 'static/assets/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'txt', 'jfif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file_key='file'):
    if file_key not in request.files:
        return {'error': 'No file part in the request'}

    file = request.files[file_key]

    if file.filename == '':
        return {'error': 'No selected file'}

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(save_path)
        return {'path': save_path}

    return {'error': 'Invalid file type'}
#emailjs credentials
EMAILJS_SERVICE_ID = os.environ.get("EMAILJS_SERVICE_ID")
EMAILJS_TEMPLATE_ID = os.environ.get("EMAILJS_TEMPLATE_ID")
EMAILJS_USER_ID = os.environ.get("EMAILJS_USER_ID")
otps = {}
#email function
def send_otp_email_via_emailjs(to_email, otp_code):
    """
    Sends an email with the OTP to the specified email address using the Email.js API.
    
    Args:
        to_email (str): The recipient's email address.
        otp_code (str): The one-time password to send.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    url = "https://api.emailjs.com/api/v1.0/email/send"
    
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_USER_ID,
        "template_params": {
            "email": to_email,
            "passcode": otp_code
        }
    }
    print(payload)
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Email sent successfully via Email.js")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending email via Email.js: {e}")
        return False
#index
@app.route("/")
def index():
    return render_template("index.html")
#bank list route
@app.route("/banks", methods=["GET"])
def get_banks():
    url = "https://api.paystack.co/bank"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        # return only needed fields
        banks = [{"name": b["name"], "code": b["code"]} for b in data.get("data", [])]
        return jsonify(banks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#new sign up
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup1.html")

    # POST (JSON)
    data = request.get_json(silent=True) or {}
    print(data)
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    bank_code = data.get("bank_code")
    account_number = data.get("account_number")

    # Basic validations
    missing = [k for k, v in {
        "name": name, "email": email, "phone": phone,
        "password": password, "bank_code": bank_code,
        "account_number": account_number
    }.items() if not v]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    if not account_number.isdigit() or len(account_number) != 10:
        return jsonify({"message": "account_number must be 10 digits"}), 400

    # 1) Resolve account (Paystack)
    verify_url = "https://api.paystack.co/bank/resolve"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    try:
        verify_res = requests.get(
            verify_url,
            params={"account_number": account_number, "bank_code": bank_code},
            headers=headers,
            timeout=15
        ).json()
    except Exception as e:
        return jsonify({"message": "Bank resolve failed", "error": str(e)}), 502

    if not verify_res.get("status"):
        return jsonify({"message": "Invalid bank details", "paystack": verify_res}), 400

    account_name = (verify_res.get("data") or {}).get("account_name")

    # 2) Create subaccount (5% platform cut)
    sub_payload = {
        "business_name": name,
        "settlement_bank": bank_code,
        "account_number": account_number,
        "percentage_charge": 5,              # your platform cut (5%)
        "primary_contact_name": name,
        "primary_contact_email": email,
        "primary_contact_phone": phone,
        "settlement_schedule": "auto"
    }
    try:
        sub_res = requests.post(
            "https://api.paystack.co/subaccount",
            json=sub_payload,
            headers={**headers, "Content-Type": "application/json"},
            timeout=15
        ).json()
    except Exception as e:
        return jsonify({"message": "Subaccount creation failed", "error": str(e)}), 502

    if not sub_res.get("status"):
        return jsonify({"message": "Could not create subaccount", "paystack": sub_res}), 400

    subaccount_code = sub_res["data"]["subaccount_code"]
    bank_name = sub_res["data"]["settlement_bank"]  # nice human-readable name

    # 3) Save to DB
    try:
        db.execute("""
            INSERT INTO users 
            (name, email, phone, password, bank_name, bank_code, account_number, account_name, subaccount_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, name, email, phone, password, bank_name, bank_code, account_number, account_name, subaccount_code)
        return {'message':"successful"}
    except Exception as e:
        return jsonify({"message": "DB insert failed", "error": str(e)}), 500


#signup
@app.route("/register_signup", methods=["GET","POST"])
def register_signup():
    if request.method == "POST":
        data =request.form
        print(data)
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        img = handle_file_upload("profile-picture")
        db.execute("INSERT INTO users(name,email,phone,password,img) VALUES(?,?,?,?,?)", name, email, phone, password, img.get("path"))
        user = db.execute("SELECT * FROM users WHERE email = ?", email)
        if user:
            print("signup successful")
            return {"response":"successful", "url":f"https://fling-2a4m.onrender.com/{user[0]['id']}"}
    return render_template("signup1.html")
# Login / Register
@app.route("/register_login", methods=["GET","POST"])
def register_login():
    if request.method =="POST":
        data = request.form
        email = data.get('email')
        password = data.get('password')
        user = db.execute("SELECT * FROM users WHERE email = ? AND password = ?", email, password)

        if user:
            print("login successful")
            # Store in session
            session["user_id"] = user[0]["id"]
            return {"response": "successful", "url": "https://fling-2a4m.onrender.com/dashboard"}
        else:
            return {"response": "unsuccessful"}

    return render_template("login.html")
#dashboard
@app.route("/dashboard/")
def dashboard():
    if "user_id" not in session:
        return redirect("/register_login")

    user_id = session["user_id"]
    format_string = "%Y-%m-%d"
    
    # Define a safe directory for deletion
    template_dir = os.path.join(os.getcwd(), "templates")
    
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    
    events = db.execute("SELECT * FROM events WHERE created_by = ?", user_id)
    
    for event in events:
        event_datetime = event['date']
        
        # Check if the event date is in the past
        if datetime.now().date() >= event_datetime:
            # Construct a safe, full file path
            file_path = os.path.join(template_dir, event["html"])
            
            # Crucial security check: Ensure the path is a subdirectory of the templates folder
            # This prevents directory traversal attacks
            if os.path.abspath(file_path).startswith(os.path.abspath(template_dir) + os.sep):
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"File '{file_path}' has been successfully deleted.")
                        
                        # Use a single database transaction for the deletions
                        db.execute("BEGIN TRANSACTION")
                        db.execute("DELETE FROM tickets WHERE event_id = ?", event['id'])
                        db.execute("DELETE FROM events WHERE id = ?", event['id'])
                        db.execute("COMMIT")
                        
                    except OSError as e:
                        print(f"Error deleting file {event['html']}: {e.strerror}")
                        db.execute("ROLLBACK")
                        return e, 500
                else:
                    print(f"Warning: File '{file_path}' does not exist.")
                    return "Warning: File '{file_path}' does not exist.", 500
            else:
                print(f"Security Alert: Attempted path traversal for file: {event['html']}")
                return f"Security Alert: Attempted path traversal for file: {event['html']}", 500
                
    # Re-fetch the updated event list after deletions
    events = db.execute("SELECT * FROM events WHERE created_by = ?", user_id)
    
    tickets = db.execute(
        "SELECT * FROM tickets JOIN events ON events.id = tickets.event_id WHERE user_id = ?",
        user_id
    )
    
    return render_template("my_dashboard.html", user=user, events=events, tickets=tickets)
# --- New Route for Event Creation ---
@app.route("/create_event/<int:user_id>", methods=["POST"])
def create_event(user_id):
    """
    Handles the creation of a new event.
    This route expects a POST request with form data and file uploads.
    """
    if request.method == "POST":
        try:
            # Retrieve form data
            format_string = "%Y-%m-%d"
            title = request.form.get("event-title")
            date = request.form.get("event-date")
            time = request.form.get("event-time")
            location = request.form.get("event-location")
            description = request.form.get("event-description")
            price = request.form.get("ticket-price") # <-- New: Retrieve price from form
            user_prompt = request.form.get("ai-template-prompt")
            # Handle file uploads using your existing function
            img1_path = upload_file_to_cloudinary("image-1").get("path")
            img2_path = upload_file_to_cloudinary("image-2").get("path")
            img3_path = upload_file_to_cloudinary("image-3").get("path")
            video_path = upload_file_to_cloudinary("video").get("path")

            #ensuring the uploaded time is not a time from the past 
            date_to_check = datetime.strptime(date, format_string)
            if datetime.now() >= date_to_check:
                return jsonify({"response":"Date is less than today's date"})

            # Ensure required fields are not empty
            if not all([title, date, time, location, description]):
                # You might want to handle this with a flash message and a redirect
                return jsonify({"error": "Please fill out all required fields"}), 400

            # Insert data into the events table
            try:
                url_key = generate_url_code()
                db.execute(
                    "INSERT INTO events (title, description, location, date, time, img1, img2, img3, video, created_by, price, url_key) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    title,
                    description,
                    location,
                    date,
                    time,
                    img1_path,
                    img2_path,
                    img3_path,
                    video_path,
                    user_id,  # The creator ID is passed from the URL
                    price,
                    url_key
                )
                #template generation
                event = db.execute("SELECT * FROM events WHERE created_by = ? and url_key = ?", user_id, url_key)
                # --- Main script execution ---
                prompt = (
                    "You are a seasoned UX/UI designer + front-end developer with 10+ years of experience in event branding. "
                    "Fluent in HTML, CSS, and JavaScript. You are emotionally intuitive, always prioritizing elegance, responsiveness, and engagement. "
                    "You love solving layout challenges, follow modern design trends, and make sure every design matches the latest standard. "
                    "Generate a responsive, modern, and mobile-friendly HTML template for an event. "
                    "Do NOT include extra commentary—output only the HTML template. "
                    "Use the uploaded picture for design inspiration (e.g., background styling) but do not insert it directly. "
                    "The template must include all necessary event info, styled with embedded CSS, and be easily customizable. "
                    "At the bottom of the page, add 'Powered by Techlite'. "
                    "Include a 'Buy Ticket' button using Jinja notation for linking. "
                    "Do NOT use media assets with 'none'. "
                    "For images and video: use the provided static file paths (forward slashes only, no Jinja for paths). "
                    "If an image/video fails to load, include an external alt source in the 'alt' attribute. "
                    "Remove Jinja from href tags including the ticket purchase link. "
                    "Hardcode all other event details. "
                    f"Current year (for footer): {datetime.now().year}. "
                    f"Event Title: {title}. "
                    f"Event Description: {description}. "
                    f"Event Time: {time}. "
                    f"Event Date: {date}. "
                    f"Event Price: {price}. "
                    f"Ticket Purchase Link: https://fling-2a4m.onrender.com/ticket_login/{event[0]['id']}. "
                    f"Image 1 Path: {img1_path}. "
                    f"Image 2 Path: {img2_path}. "
                    f"Image 3 Path: {img3_path}. "
                    f"Video Path: {video_path}. "
                    f"Additional user instructions: {user_prompt}."
                )

                # Generate the ticket template
                html_result = generate_ticket_template(prompt)

                if html_result:
                    # Print the generated HTML code
                    print("----PROMPT----")
                    print(prompt)
                    print("--- Generated HTML Template ---")
                    print(html_result)
                    print("--- Just HTML Template ---")
                    html_result=html_result.replace('```', '')
                    print(html_result)
                    #save_html(html_result,f"{event[0]['title']}{event[0]['url_key']}.html",  'templates')
                    db.execute("UPDATE events SET html = ? wHERE id = ?", f"{html_result}", f"{event[0]['id']}")
                    return jsonify([{"response":"successful", "event_link":f"https://fling-2a4m.onrender.com/view_event/{event[0]['url_key']}"}])
                else:
                    print("Could not generate HTML template.")
            except Exception as e:
                # Consider more robust error handling and logging
                return jsonify({"error": f"An error occurred: {e}"}), 500
        except Exception as e:
            return {'response':f"{e}"}
    # If GET request, you might want to return the form page
    return redirect(url_for("dashboard", user_id=user_id))
@app.route("/view_event/<url_key>")
def view_event(url_key):
    event = db.execute("SELECT * FROM events WHERE url_key = ?", url_key)
    if event:
        html_content = event[0]['html']
        # Return the raw HTML with the correct Content-Type header
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
@app.route("/get_user_events/<int:id>")
def get_user_events(id):
    events = db.execute("SELECT * FROM events WHERE created_by = ?", id)
    if events:
        # Iterate through the list of events to format the date and time keys
        for event in events:
            # Convert the 'date' key to a string
            if 'date' in event and isinstance(event['date'], date):
                event['date'] = event['date'].strftime("%Y-%m-%d")

            # Convert the 'time' key to a string
            if 'time' in event and isinstance(event['time'], time):
                event['time'] = event['time'].strftime("%H:%M:%S")

            # Convert the 'created_at' key to a string
            if 'created_at' in event and isinstance(event['created_at'], datetime):
                event['created_at'] = event['created_at'].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify(events)
    else:
        return jsonify([])

@app.route("/track_events/<key>")
def track_events(key):
    event = db.execute("SELECT * FROM events JOIN users ON events.created_by = users.id WHERE url_key = ?", key)[0]
    tickets = db.execute("SELECT * FROM users JOIN events ON users.id = events.created_by JOIN tickets ON users.id=tickets.user_id WHERE url_key =?", key)
    return render_template("track_events.html", tickets=tickets, event=event)

@app.route("/sales_data/<id>")
def sales_data(id):
    try:
        chart_data = {"x": [], "y": []}
        today = datetime.now()
        format_string = "%Y-%m-%d"

        # Get event creation date
        event_created_date = db.execute(
            """SELECT events.created_at 
            FROM tickets 
            JOIN events ON events.id = tickets.event_id 
            JOIN users ON users.id = tickets.user_id 
            WHERE events.id = ?""", id
        )[0]['created_at']
        datetime_object = datetime.strptime(event_created_date, format_string)

        # Get tickets
        tickets = db.execute(
            """SELECT events.created_at 
            FROM tickets 
            JOIN events ON events.id = tickets.event_id 
            JOIN users ON users.id = tickets.user_id 
            WHERE events.id = ?""",
        id)

        # Build daily sales counts
        day_diff = (today - datetime_object).days
        for i in range(day_diff + 1):  # include today
            day = (datetime_object + timedelta(days=i)).date()
            chart_data["x"].append(day.strftime("%Y-%m-%d"))

            # Count tickets created on this day
            sales_count = sum(
                1 for ticket in tickets
                if datetime.strptime(ticket['created_at'], format_string).date() == day
            )
            chart_data["y"].append(sales_count)
        print(chart_data)
        return chart_data
    except IndexError:
        return {"x": [], "y": []}


@app.route("/search_attendees", methods=["POST"])
def search_attendees():
    data = request.get_json()
    query = data.get("query", "").lower()

    filtered = []
    attendees = db.execute("SELECT users.name, users.email, events.price \
                            FROM tickets JOIN users ON users.id = tickets.user_id \
                            JOIN events ON events.id = tickets.event_id")

    for attendee in attendees:
        if (query in attendee["name"].lower() 
            or query in attendee["email"].lower() 
            or query in str(attendee["price"]).lower()):
            filtered.append({
                "name": attendee["name"],
                "email": attendee["email"],
                "price": attendee["price"]
            })

    return jsonify({"attendees": filtered})
@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    if request.method == "POST":
        data = request.get_json()
        print(data)
        user_prompt = data.get("prompt")
        event_id = data.get("event_id")
        BASE_PROMPT = """
        You are an event sales assistant. you engage the user provide advice and insight based on the event data and talk about other things 
        Answer ONLY based on the provided database data. 
        Do not invent data. 
        Be concise, clear, and numeric where possible.
        
        """

        #tickets
        data = db.execute("SELECT users.name, users.email, events.price, tickets.created_at  FROM tickets JOIN events ON tickets.event_id = events.id JOIN users ON tickets.user_id = users.id WHERE events.id = ?", event_id)
        print(data)
        info = ""
        for row in data:
            info+=(f"{row['name']}-{row['email']}-{row['price']}-{row['created_at']}")
        # Combine with base instructions
        full_prompt = BASE_PROMPT + "\nprompt: " + user_prompt + "\nevent purchase data/ticket sales: " + info
        #full_prompt = full_prompt.join(info)
        #sending and receiving AI response
        result = generate_ticket_template(full_prompt)
        if result:
            print("prompt", full_prompt)
            return jsonify({"response": f"{result}"})
        else:
            return jsonify({"response": f"An error occured with the model, contact manufacturer"})
@app.route("/buy_ticket/<int:id>")
def buy_ticket(id):
    return render_template("")
@app.route("/ticket_login/<int:id>", methods=["GET","POST"])
def ticket_login(id):
    if request.method =="POST":
        data = request.get_json()
        print(data)
        email = data.get('email')
        password = data.get('password')
        user = db.execute("SELECT * FROM users WHERE email = ? AND password = ?", email, password)
        if user:
            print("login successful",user)
            return {"response":"successful", "user_id":f"{user[0]['id']}", "event_id":f"{id}", "user_email":f"{email}"}
        else:
            print("unsuccessful")
            return {"response":"unsuccessful"}
    event = db.execute("SELECT * FROM events WHERE id = ?", id)[0]
    print(event)
    return render_template("buy_ticket.html", event=event)
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
# 🔥 Step 1: Post session and initialize Paystack payment
@app.route('/paystack_init', methods=['POST'])
def post_session():
    try:
        data = request.form
        print(data)
        event_id = data.get("event_id")
        user_id = data.get("user_id")
        email = data.get("user_email")
        price = data.get("event_price")
        subaccount = db.execute("SELECT subaccount_code FROM users WHERE id = ? ", user_id)
        metadata = {
            "event_id":event_id,
            "user_id":user_id
        }

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "email": email,
            "amount": int(float(price) * 100),  # Paystack wants kobo
            "metadata": metadata,
            "callback_url": "https://fling-2a4m.onrender.com/callback",

            # 👇 Revenue sharing
            "subaccount": subaccount[0]['subaccount_code'],  # seller's subaccount
            "bearer": "subaccount",  # who bears Paystack fees (main or subaccount)
            "transaction_charge": int(float(price) * 100 * 0.05)  # 5% cut for you
        }


        response = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=headers)
        print(response)
        res_data = response.json()
        if res_data.get("status"):
            print(res_data) # This print is already there, you can keep it or remove it
            return redirect(res_data['data']['authorization_url'])

        else:
            print({"error": res_data})
            return {"error": res_data}
    except Exception as e:
        return {"error": str(e)}


# 🔁 Step 2: Payment verification callback
@app.route('/callback')
def callback():
    reference = request.args.get('reference')

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    response_data = res.json()

    if not response_data.get('status'):
        return {"error": "Payment verification failed"}

    payment_data = response_data['data']
    metadata = payment_data['metadata']

    try:
        code = generate_code()
        if db.execute("INSERT INTO tickets(user_id, event_id, ticket_code) VALUES(?,?,?)",metadata["user_id"], metadata["event_id"], code):
            return render_template('success.html', home=f"https://fling-2a4m.onrender.com/dashboard")  # or return a JSON response
    except IndexError as e:
        return {"error": str(e)}
@app.route("/validation/<key>", methods=["GET", "POST"])
def validation(key):
    if request.method == "POST":
        data = request.get_json()
        print(data)
        code = data['code']
        key = data['key']
        event = db.execute("SELECT * FROM events WHERE url_key = ?", key)
        print(code)
        valid = db.execute("SELECT * FROM tickets WHERE ticket_code = ? AND event_id = ?", code, event[0]['id'])
        print(valid)
        if valid:
            if valid[0]['status'] == "valid":
                print("yip")
                db.execute("UPDATE tickets SET status = ? WHERE ticket_code = ? AND event_id = ?", "used", code, event[0]['id'])
                return {"response":"valid"}
            else:
                return {"response":"used"}
        else:
            return {"response":"invalid"}
    event = db.execute("SELECT * FROM events WHERE url_key = ?", key)[0]
    return render_template("validity.html", event = event)
@app.route("/request_otp", methods=["POST"])
def request_otp():
    """
    Generates an OTP and sends it to the user's email via Email.js.
    """
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"response": "error", "message": "Email is required"}), 400

        # Generate a 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store the OTP with the email
        otps[email] = otp_code

        # Send the email with the OTP
        if send_otp_email_via_emailjs(email, otp_code):
            return jsonify({"response": "sent", "message": "OTP sent successfully"}), 200
        else:
            return jsonify({"response": "error", "message": "Failed to send OTP"}), 500

    except Exception as e:
        return jsonify({"response": "error", "message": str(e)}), 500
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    """
    Verifies the OTP sent by the user.
    """
    try:
        data = request.get_json()
        email = data.get("email")
        otp = data.get("otp")
        exist = db.execute("SELECT * FROM users WHERE email = ?", email)
        # Check if the OTP matches the one stored in our temporary "database"
        if exist:
            if email in otps and otps[email] == otp:
                del otps[email] # Delete the OTP after successful verification
                # Store in session
                session["user_id"] = user[0]["id"]
                return jsonify({"response": "verified", "url": "/dashboard"}), 200
            else:
                return jsonify({"response": "error", "message": "Invalid OTP"}), 401
        else:
            return jsonify({"response": "error", "message": "Unknown email"}), 401

    except Exception as e:
        return jsonify({"response": "error", "message": str(e)}), 500
@app.route("/update_profile", methods=["POST"])
def update_profile():
    try:
        data = request.get_json()

        # Extract form fields
        user_id = data.get("id") or session.get("user_id")  # fallback to session
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")
        account_name = data.get("account_name")

        # Check required fields
        if not all([user_id, name, email, password, phone, bank_code, account_number]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Update DB
        db.execute("""
            UPDATE users
            SET name = ?, email = ?, password = ?, phone = ?, 
                bank_code = ?, account_number = ?, account_name = ?
            WHERE id = ?
        """, name, email, password, phone, bank_code, account_number, account_name, user_id)

        return jsonify({"status": "success", "message": "Profile updated successfully!"})

    except Exception as e:
        print("❌ Error updating profile:", e)
        return jsonify({"status": "error", "message": "Server error"}), 500

@app.route("/retrieval")
def retrieval():
    return render_template("retrieval.html")
if __name__=="__main__":
    app.run(debug=True, port=1000 )
