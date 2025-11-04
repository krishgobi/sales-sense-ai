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
users = db.users_update

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
    return render_template('labor.html', logged_in='user_id' in session)

@app.route('/labor/register', methods=['POST'])
def labor_register():
    email = request.form.get('email')
    name = request.form.get('name')
    mobile = request.form.get('mobile')

    # Validate input
    if not email or not name or not mobile:
        flash('All fields are required', 'error')
        return redirect(url_for('labor_panel'))

    # Check if email or mobile already exists
    if users.find_one({'$or': [{'email': email}, {'mobile': mobile}]}):
        flash('Email or mobile number already registered', 'error')
        return redirect(url_for('labor_panel'))

    # Create new user
    user = {
        'email': email,
        'name': name,
        'mobile': mobile
    }
    
    result = users.insert_one(user)
    if result.inserted_id:
        # Send welcome email
        if send_welcome_email(email, name):
            flash('Registration successful! Welcome email sent.', 'success')
        else:
            flash('Registration successful! But email could not be sent.', 'warning')
        
        session['user_id'] = str(result.inserted_id)
        return redirect(url_for('user_products'))
    
    flash('Registration failed', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/labor/login', methods=['POST'])
def labor_login():
    identifier = request.form.get('identifier')  # This can be email or mobile
    
    # Try to find user by email or mobile
    user = users.find_one({
        '$or': [
            {'email': identifier},
            {'mobile': identifier}
        ]
    })
    
    if user:
        session['user_id'] = str(user['_id'])
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('user_products'))
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/user/products')
def user_products():
    if 'user_id' not in session:
        return redirect(url_for('labor_panel'))
    
    user = users.find_one({'_id': ObjectId(session['user_id'])})
    all_products = list(products.find())
    return render_template('user_products.html', products=all_products, user=user)

@app.route('/labor/logout')
def labor_logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('labor_panel'))

if __name__ == '__main__':
    app.run(debug=True)