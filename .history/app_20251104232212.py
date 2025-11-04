from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

# Email configuration
def send_welcome_email(user_email, user_name):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = user_email
        msg['Subject'] = 'Welcome to SalesSense!'

        body = f"""
        Dear {user_name},

        Welcome to SalesSense! We're excited to have you as a new member.
        You can now browse our products and make purchases through our platform.

        Best regards,
        The SalesSense Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Collections
products = db.products
workers = db.workers
labors = db.labors
admins = db.admins

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products')
def product_list():
    # Fetch products from database
    all_products = list(products.find())
    return render_template('products.html', products=all_products)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/worker')
def worker_panel():
    return render_template('worker.html')

@app.route('/labor')
def labor_panel():
    return render_template('labor.html')

if __name__ == '__main__':
    app.run(debug=True)