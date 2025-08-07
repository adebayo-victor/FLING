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

#loading virtual environment
load_dotenv()
#Initiating app ...
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("app_secret_key")
db = SQL('sqlite:///info.db')
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
@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user = db.execute("SELECT * FROM users WHERE id =?", user_id)
    if user:
        return render_template("my_dashboard.html", user=user)
if __name__=="__main__":
    app.run(debug=True, port=1000 )