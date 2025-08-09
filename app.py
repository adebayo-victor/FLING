import random
import csv
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_file
import pandas as pd
from flask_cors import CORS
from cs50 import SQL
import secrets
import os
from werkzeug.utils import secure_filename
import string
import io
import xlsxwriter
from dotenv import load_dotenv
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
db = SQL('sqlite:///info.db')
#gemini prompt functions
API_KEY = os.environ.get("gemini_key")
if not API_KEY:
    print("Error: Gemini API key not found. Please set 'gemini_key' in your .env file.")
    exit()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

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
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=data)
        
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
            return {"response":"successful", "url":f"https://hhxsq4xb-1000.uks1.devtunnels.ms/{user[0]['id']}"}
    return render_template("signup.html")
@app.route("/register_login", methods=["GET","POST"])
def register_login():
    if request.method =="POST":
        data = request.form
        email = data.get('email')
        password = data.get('password')
        user = db.execute("SELECT * FROM users WHERE email = ? AND password = ?", email, password)
        if user:
            print("signup successful")
            return {"response":"successful", "url":f"https://hhxsq4xb-1000.uks1.devtunnels.ms/dashboard/{user[0]['id']}"}
        else:
            return {"response":"unsuccessful"}
    return render_template("login.html")
#dashboard
@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user = db.execute("SELECT * FROM users WHERE id =?", user_id)[0]
    if user:
        return render_template("my_dashboard.html", user=user)
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
            title = request.form.get("event-title")
            date = request.form.get("event-date")
            time = request.form.get("event-time")
            location = request.form.get("event-location")
            description = request.form.get("event-description")
            price = request.form.get("ticket-price") # <-- New: Retrieve price from form
            user_prompt = request.form.get("ai-template-prompt")
            # Handle file uploads using your existing function
            img1_path = handle_file_upload("image-1").get("path")
            img2_path = handle_file_upload("image-2").get("path")
            img3_path = handle_file_upload("image-3").get("path")
            video_path = handle_file_upload("video").get("path")

            # Note: The `aiTemplatePrompt` and `status` keys from your description
            # are not being stored in the `events` table because your provided schema
            # does not include columns for them.

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
                prompt = "You are seasoned UX/UI designer + front-end dev with 10+ years in event branding. Fluent in HTML/CSS & JS, emotionally intuitive, always priotizing elegance, responsiveness, and engagement. Loves solving layout challenges and follows modern design trends and tends to lean toward improving and making sure it matches the latest trend.Generate a responsive, modern and mobile-friendly HTML template for events. The template must include all necessary info for the event, styled with embedded CSS and easily customizable, generate just the requested template, nothing else and at the bottom of every website u design add a 'Powered by Techlite' at the end of every website you generate and add a button for buying the ticket for the event, by using jinja notation/syntax, add the file paths for the image and the video and add a alt argument link from an external source to complement it if it dosen't show via the src argument which are in the server's static folder, use jinja notation for the image and video paths only,change the backward slash to forward slashes , hard code the rest the info to be added are as follows:"
                prompt += f'''{user_prompt}
                    event-title: {title},
                    event-description:{description},
                    event-time:{time},
                    event-date:{date},
                    event-price:{price},
                    ticket-purchase-link:https://hhxsq4xb-1000.uks1.devtunnels.ms/buy_ticket/{event[0]['id']},
                    img-1 path: {img1_path},
                    img-1 path: {img2_path},
                    img-1 path: {img3_path},
                    video-path: {video_path},
                '''
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
                    save_html(html_result,f"{event[0]['title']}{event[0]['url_key']}.html",  'templates')
                    db.execute("UPDATE events SET html = ? wHERE id = ?", f"{event[0]['title']}{event[0]['url_key']}.html", f"{event[0]['id']}")
                    return jsonify([{"response":"successful", "event_link":f"https://hhxsq4xb-1000.uks1.devtunnels.ms/view_event/{event[0]['url_key']}"}])
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
        return render_template(event[0]['html'])
if __name__=="__main__":
    app.run(debug=True, port=1000 )