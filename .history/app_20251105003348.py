from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
from bson import ObjectId
from functools import wraps
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import datetime
from decimal import Decimal

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# MongoDB connection setup with error handling
def get_database_connection():
    try:
        # Get MongoDB connection details from environment variables
        mongodb_url = os.getenv('MONGODB_URL')
        database_name = os.getenv('MONGODB_DATABASE')
        
        if not mongodb_url or not database_name:
            raise ValueError("MongoDB connection details not found in environment variables")
        
        # Set up MongoDB client with proper configurations
        client = MongoClient(
            mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=50,
            retryWrites=True,
            retryReads=True
        )
        
        # Test the connection
        client.admin.command('ping')
        
        # Get database
        db = client[database_name]
        return db
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        print("Please check your MongoDB connection string and ensure the service is running.")
        print("Also check if your IP address is whitelisted in MongoDB Atlas.")
        raise

try:
    db = get_database_connection()
except Exception as e:
    print("Failed to establish MongoDB connection. Starting with limited functionality.")
    db = None  # We'll handle this case in our routes

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

# Helper functions for safe calculations
def extract_numeric_value(value):
    """Extract numeric value from strings like '1kg', '500g', etc."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove commas and any currency symbols
            value = str(value).replace(',', '').replace('$', '').strip()
            
            # Try direct conversion first
            try:
                return float(value)
            except ValueError:
                # If direct conversion fails, try to extract numeric part
                import re
                numeric_parts = re.findall(r'[-+]?\d*\.\d+|\d+', value)
                if numeric_parts:
                    # Take the first number found
                    return float(numeric_parts[0])
        return 0.0
    except Exception as e:
        print(f"Error extracting numeric value from {value}: {e}")
        return 0.0

def safe_float(value, default=0.0):
    """Safely convert a value to float"""
    try:
        if isinstance(value, str):
            # Remove any currency symbols and commas
            value = value.replace('$', '').replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_sale_amount(sale):
    """Safely calculate sale amount from either total_price or price * quantity"""
    try:
        # If total_price exists and is valid, use it
        if sale.get('total_price'):
            return safe_float(sale['total_price'])
        
        # Otherwise calculate from price and quantity
        price = safe_float(sale.get('price', 0))
        
        # Handle quantity conversion
        try:
            # First try to convert directly to float
            quantity = float(str(sale.get('quantity', '0')).replace(',', ''))
        except (ValueError, TypeError):
            # If that fails, try to extract numeric value
            quantity = extract_numeric_value(sale.get('quantity', 0))
        
        # Ensure we have valid numbers
        if not isinstance(quantity, (int, float)):
            quantity = 0
        if not isinstance(price, (int, float)):
            price = 0
            
        return float(price) * float(quantity)
    except Exception as e:
        print(f"Error calculating sale amount for sale {sale.get('_id', 'unknown')}: {e}")
        return 0.0

# Collections
products_update = db.products_update
workers_update = db.workers_update  # Changed from workers to workers_update
worker_specific_added = db.worker_specific_added  # New collection for worker actions
labors = db.labors
admins = db.admins
users = db.users_update
products_sold = db.products_sold
products_by_user = db.products_by_user

# Custom template filters
@app.template_filter('safe_sum')
def safe_sum(variants, attribute):
    """Safely sum up values from a list of dictionaries"""
    if not variants:
        return 0
    return sum(variant.get(attribute, 0) for variant in variants if isinstance(variant, dict))

@app.template_filter('format_date')
def format_date(date, format='%Y-%m-%d'):
    """Safely format a date"""
    try:
        if date:
            return date.strftime(format)
        return ''
    except:
        return ''

@app.template_filter('safe_get')
def safe_get(obj, key, default=''):
    """Safely get a value from a dictionary"""
    if not isinstance(obj, dict):
        return default
    return obj.get(key, default)

# Email Templates
def send_purchase_confirmation_email(user_email, user_name, order_details):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = user_email
        msg['Subject'] = 'Your SalesSense Purchase Confirmation'

        body = f"""
        Dear {user_name},

        Thank you for your purchase! Here are your order details:

        {order_details}

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
        print(f"Error sending purchase confirmation email: {e}")
        return False

def send_worker_credentials_email(worker_email, worker_name, password):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = worker_email
        msg['Subject'] = 'Welcome to SalesSense - Your Worker Account Credentials'

        body = f"""
        Dear {worker_name},

        Your worker account has been created in SalesSense. Here are your login credentials:

        Username: {worker_email}
        Password: {password}

        Please login at the worker portal and change your password upon first login.

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
        print(f"Error sending worker credentials email: {e}")
        return False

# Database connection check decorator
def require_db_connection(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if db is None:
            flash("Database connection is currently unavailable. Please try again later.", "error")
            return render_template('error.html', 
                                error="Database Connection Error",
                                message="Unable to connect to the database. Please try again later.")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_db_connection
def home():
    return render_template('home.html')

@app.route('/products')
def product_list():
    # Fetch products from database
    all_products = list(products_update.find())
    return render_template('products.html', products=all_products)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('admin_login'))
        
        # Check session timeout (30 minutes)
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.datetime.fromtimestamp(last_activity)
            if (datetime.datetime.utcnow() - last_activity_time).seconds > 1800:  # 30 minutes
                session.clear()
                flash('Session expired. Please login again.', 'error')
                return redirect(url_for('admin_login'))
        
        # Update last activity
        session['last_activity'] = datetime.datetime.utcnow().timestamp()
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
def admin_route():
    # Check if user is authenticated
    if 'admin_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('admin_login'))
    
    # Check session timeout
    last_activity = session.get('last_activity')
    if last_activity:
        last_activity_time = datetime.datetime.fromtimestamp(last_activity)
        if (datetime.datetime.utcnow() - last_activity_time).seconds > 1800:  # 30 minutes
            session.clear()
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('admin_login'))
    
    # Update last activity and proceed to admin panel
    session['last_activity'] = datetime.datetime.utcnow().timestamp()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Get statistics
    stats = {
        'total_users': users.count_documents({}),
        'new_users_today': users.count_documents({
            'created_at': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        }),
        'total_sales': sum(calculate_sale_amount(sale) for sale in products_sold.find()),
        'sales_today': sum(calculate_sale_amount(sale) for sale in products_sold.find({
            'date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        })),
        'total_products': products_update.count_documents({}),
        'low_stock_products': sum(1 for product in products_update.find() 
                                for variant in product.get('variants', []) 
                                if isinstance(variant, dict) and variant.get('stock', 0) < 10),
        'total_workers': workers_update.count_documents({}),
        'active_workers': workers_update.count_documents({
            'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
        })
    }

    # Get user data
    users_data = list(users.find().sort('join_date', -1).limit(10))
    for user in users_data:
        user_orders = list(products_sold.find({'user_id': user['_id']}))
        user['orders'] = user_orders
        user['total_spent'] = sum(calculate_sale_amount(order) for order in user_orders)

    # Get product data
    products_data = list(products_update.find())

    # Get worker data
    workers_data = list(workers_update.find())
    for worker in workers_data:
        worker['products_added'] = list(worker_specific_added.find({'worker_id': worker['_id']}))

    # Get sales data for chart
    today = datetime.datetime.now()
    past_week = today - datetime.timedelta(days=7)
    sales_by_date = {}
    for sale in products_sold.find({'date': {'$gte': past_week}}):
        date_str = sale['date'].strftime('%Y-%m-%d')
        if date_str not in sales_by_date:
            sales_by_date[date_str] = 0
        # Calculate sale amount using helper function
        sale_amount = calculate_sale_amount(sale)
        sales_by_date[date_str] += sale_amount

    sales_data = {
        'dates': list(sales_by_date.keys()),
        'values': list(sales_by_date.values())
    }

    # Get category data for chart
    category_sales = {}
    for sale in products_sold.find():
        product = products_update.find_one({'_id': sale['product_id']})
        if product:
            category = product.get('category', 'Uncategorized')
            if category not in category_sales:
                category_sales[category] = 0
            # Calculate sale amount using helper function
            sale_amount = calculate_sale_amount(sale)
            category_sales[category] += sale_amount

    category_data = {
        'labels': list(category_sales.keys()),
        'values': list(category_sales.values())
    }

    # Get top selling products
    top_products = []
    product_sales = {}
    for sale in products_sold.find():
        if sale['product_id'] not in product_sales:
            product_sales[sale['product_id']] = {
                'name': sale.get('product_name', 'Unknown Product'),
                'units_sold': 0,
                'revenue': 0
            }
        try:
            # Convert quantity to integer, defaulting to 0 if invalid
            quantity = int(float(str(sale.get('quantity', '0')).replace(',', '')))
            product_sales[sale['product_id']]['units_sold'] += quantity
            
            # Calculate sale amount using our helper function
            sale_amount = calculate_sale_amount(sale)
            product_sales[sale['product_id']]['revenue'] += sale_amount
        except (ValueError, TypeError) as e:
            print(f"Error processing sale {sale.get('_id')}: {str(e)}")
            continue

    top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:5]

    return render_template('admin_dashboard.html',
                         stats=stats,
                         users=users_data,
                         products=products_data,
                         workers=workers_data,
                         sales_data=sales_data,
                         category_data=category_data,
                         top_products=top_products)

@app.route('/admin/create-worker', methods=['POST'])
def create_worker():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')  # In production, generate a random password

        if not name or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('admin_dashboard'))

        # Check if worker already exists
        if workers_update.find_one({'email': email}):
            flash('Worker with this email already exists', 'error')
            return redirect(url_for('admin_dashboard'))

        # Create new worker
        worker = {
            'name': name,
            'email': email,
            'password': password,  # In production, hash this password
            'created_at': datetime.datetime.utcnow(),
            'total_products_added': 0
        }

        try:
            result = workers_update.insert_one(worker)
            if result.inserted_id:
                # Send credentials email
                if send_worker_credentials_email(email, name, password):
                    flash('Worker created successfully and credentials sent', 'success')
                else:
                    flash('Worker created but email could not be sent', 'warning')
                return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'Error creating worker: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-email', methods=['POST'])
def admin_send_email():
    if request.method == 'POST':
        recipient_type = request.form.get('recipientType')
        subject = request.form.get('subject')
        content = request.form.get('content')
        attachment = request.files.get('attachment')

        recipients = []
        if recipient_type == 'all_users':
            recipients = [user['email'] for user in users.find()]
        elif recipient_type == 'all_workers':
            recipients = [worker['email'] for worker in workers_update.find()]
        else:  # custom recipients
            recipients = [email.strip() for email in request.form.get('customRecipients').split(',')]

        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('SENDER_EMAIL')
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'html'))

            if attachment:
                from email.mime.application import MIMEApplication
                part = MIMEApplication(
                    attachment.read(),
                    Name=attachment.filename
                )
                part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
                msg.attach(part)

            server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
            server.starttls()
            server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
            
            for recipient in recipients:
                msg['To'] = recipient
                server.send_message(msg)
            
            server.quit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/admin/export-data', methods=['POST'])
def admin_export_data():
    try:
        data = request.get_json()
        data_types = data['data_types']
        format = data['format']

        export_data = {}
        if 'users' in data_types:
            export_data['users'] = list(users.find({}, {'password': 0}))
        if 'orders' in data_types:
            export_data['orders'] = list(products_sold.find())
        if 'products' in data_types:
            export_data['products'] = list(products_update.find())

        if format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            for data_type, items in export_data.items():
                writer.writerow([f"--- {data_type.upper()} ---"])
                if items:
                    # Write headers
                    writer.writerow(items[0].keys())
                    # Write data
                    for item in items:
                        writer.writerow(item.values())
                writer.writerow([])  # Empty row between sections

            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=export.csv'
            }
        
        elif format == 'excel':
            import pandas as pd
            import io

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for data_type, items in export_data.items():
                    df = pd.DataFrame(items)
                    df.to_excel(writer, sheet_name=data_type.capitalize(), index=False)

            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': 'attachment; filename=export.xlsx'
            }
        
        elif format == 'pdf':
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            import io

            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            for data_type, items in export_data.items():
                elements.append(Paragraph(f"{data_type.upper()}", styles['Heading1']))
                if items:
                    data = [[str(k) for k in items[0].keys()]]
                    for item in items:
                        data.append([str(v) for v in item.values()])
                    t = Table(data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)

            doc.build(elements)
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': 'attachment; filename=export.pdf'
            }

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reset-worker-password/<worker_id>', methods=['POST'])
def admin_reset_worker_password(worker_id):
    try:
        worker = workers_update.find_one({'_id': ObjectId(worker_id)})
        if not worker:
            return jsonify({'error': 'Worker not found'}), 404

        # Generate random password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        # Update worker password
        workers_update.update_one(
            {'_id': ObjectId(worker_id)},
            {'$set': {'password': new_password}}  # In production, hash this password
        )

        # Send email with new password
        if send_worker_credentials_email(worker['email'], worker['name'], new_password):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Password reset but email could not be sent'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/deactivate-worker/<worker_id>', methods=['POST'])
def admin_deactivate_worker(worker_id):
    try:
        result = workers_update.update_one(
            {'_id': ObjectId(worker_id)},
            {'$set': {'status': 'inactive', 'deactivated_at': datetime.datetime.utcnow()}}
        )
        if result.modified_count:
            return jsonify({'success': True})
        return jsonify({'error': 'Worker not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete-product/<product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    try:
        result = products_update.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count:
            return jsonify({'success': True})
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/logout')
def admin_logout():
    # Log the logout event
    if 'admin_id' in session:
        print(f"Admin {session.get('admin_name')} logged out at {datetime.datetime.utcnow()}")
    
    # Clear all session data
    session.clear()
    
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Check if already logged in
    if 'admin_id' in session:
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic input validation
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('admin_login.html')

        # Add rate limiting for failed attempts
        failed_attempts = session.get('failed_attempts', 0)
        last_attempt = session.get('last_attempt_time')
        
        if last_attempt:
            last_attempt = datetime.datetime.fromtimestamp(last_attempt)
            if failed_attempts >= 5 and (datetime.datetime.utcnow() - last_attempt).seconds < 300:
                flash('Too many failed attempts. Please try again in 5 minutes.', 'error')
                return render_template('admin_login.html')

        admin = admins.find_one({'email': email})
        if not admin:
            session['failed_attempts'] = failed_attempts + 1
            session['last_attempt_time'] = datetime.datetime.utcnow().timestamp()
            flash('Invalid credentials', 'error')
            return render_template('admin_login.html')

        # Verify password (in production, use proper password hashing)
        if admin.get('password') != password:
            session['failed_attempts'] = failed_attempts + 1
            session['last_attempt_time'] = datetime.datetime.utcnow().timestamp()
            flash('Invalid credentials', 'error')
            return render_template('admin_login.html')
            
        # Clear failed attempts on successful login
        session.pop('failed_attempts', None)
        session.pop('last_attempt_time', None)
        
        # Set session with timeout
        session['admin_id'] = str(admin['_id'])
        session['admin_name'] = admin.get('name', 'Admin')
        session['login_time'] = datetime.datetime.utcnow().timestamp()
        session['last_activity'] = datetime.datetime.utcnow().timestamp()
        
        # Log successful login
        print(f"Admin login successful for {email} at {datetime.datetime.utcnow()}")
        
        flash('Login successful!', 'success')
        return redirect(url_for('admin_panel'))
        
    return render_template('admin_login.html')

@app.route('/worker')
def worker_panel():
    return render_template('worker.html')

@app.route('/worker/login', methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        worker = workers_update.find_one({'email': email})
        if worker and worker['password'] == password:  # In production, use proper password hashing
            session['worker_id'] = str(worker['_id'])
            session['worker_name'] = worker['name']
            flash('Login successful!', 'success')
            return redirect(url_for('worker_dashboard'))
        
        flash('Invalid credentials', 'error')
    return render_template('worker_login.html')

@app.route('/worker/dashboard')
def worker_dashboard():
    if 'worker_id' not in session:
        return redirect(url_for('worker_login'))
    
    # Get worker's information and statistics
    worker_id = ObjectId(session['worker_id'])
    worker = workers_update.find_one({'_id': worker_id})
    
    # Get all products
    products = list(products_update.find())
    
    # Extract unique categories
    categories = list(set(product['category'] for product in products))
    
    # Get worker's recent activities
    recent_activities = list(worker_specific_added.find(
        {'worker_id': worker_id}
    ).sort('date', -1).limit(5))
    
    return render_template('worker_dashboard.html', 
                         worker=worker,
                         products=products,
                         categories=categories,
                         recent_activities=recent_activities)

@app.route('/worker/add-product', methods=['POST'])
def add_product():
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        product = {
            'name': data['name'],
            'category': data['category'],
            'variants': data['variants'],
            'added_by': ObjectId(session['worker_id']),
            'added_at': datetime.datetime.utcnow()
        }
        
        # Insert the product
        result = products_update.insert_one(product)
        
        # Record the worker's action
        worker_action = {
            'worker_id': ObjectId(session['worker_id']),
            'product_id': result.inserted_id,
            'product_name': data['name'],
            'action_type': 'add_product',
            'date': datetime.datetime.utcnow(),
            'product_details': {
                'category': data['category'],
                'variants_count': len(data['variants'])
            }
        }
        worker_specific_added.insert_one(worker_action)
        
        # Update worker's statistics
        workers_update.update_one(
            {'_id': ObjectId(session['worker_id'])},
            {'$inc': {'total_products_added': 1}}
        )
        
        result = products_update.insert_one(product)
        return jsonify({'success': True, 'product_id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
    all_products = list(products_update.find())
    cart = session.get('cart', {})
    return render_template('user_products.html', products=all_products, user=user, cart=cart)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401

    try:
        data = request.get_json()
        product_id = data['product_id']
        selected_variants = data['selected_variants']

        product = products_update.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Invalid product'}), 400

        # Initialize cart if it doesn't exist
        if 'cart' not in session:
            session['cart'] = {}

        for variant_data in selected_variants:
            variant_index = int(variant_data['variant_index'])
            quantity = int(variant_data['quantity'])

            if variant_index >= len(product['variants']):
                return jsonify({'error': 'Invalid variant'}), 400

            variant = product['variants'][variant_index]
            if variant['stock'] < quantity:
                return jsonify({
                    'error': f'Not enough stock available for {product["name"]} ({variant["quantity"]})'
                }), 400

            cart_key = f"{product_id}_{variant_index}"
            if cart_key in session['cart']:
                # Update existing cart item
                new_quantity = session['cart'][cart_key]['quantity'] + quantity
                if new_quantity > variant['stock']:
                    return jsonify({
                        'error': f'Cannot add {quantity} more of {product["name"]} ({variant["quantity"]}). Stock limit exceeded.'
                    }), 400
                session['cart'][cart_key]['quantity'] = new_quantity
            else:
                # Add new cart item
                session['cart'][cart_key] = {
                    'product_id': product_id,
                    'product_name': product['name'],
                    'variant_index': variant_index,
                    'variant_quantity': variant['quantity'],
                    'price': variant['price'],
                    'quantity': quantity,
                    'cart_key': cart_key
                }

        session.modified = True
        
        # Calculate total items and amount
        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        cart_items = len(session['cart'])
        
        return jsonify({
            'message': 'Items added to cart successfully',
            'cart_total': cart_total,
            'cart_items': cart_items
        })

        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        return jsonify({
            'success': True,
            'message': f'Added {quantity} {product["name"]} ({variant["quantity"]}) to cart',
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401

    try:
        data = request.get_json()
        cart_key = data['cart_key']

        if 'cart' in session and cart_key in session['cart']:
            del session['cart'][cart_key]
            session.modified = True

        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        return jsonify({
            'success': True,
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/cart/view')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('labor_panel'))

    cart = session.get('cart', {})
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, cart_total=cart_total)

@app.route('/user/purchase', methods=['POST'])
def purchase_product():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        payment_method = data['payment_method']
        cart = session.get('cart', {})

        if not cart:
            return jsonify({'error': 'Cart is empty'}), 400

        user = users.find_one({'_id': ObjectId(session['user_id'])})
        purchases = []
        total_amount = 0

        # Verify stock and create purchase records
        for cart_key, item in cart.items():
            product = products_update.find_one({'_id': ObjectId(item['product_id'])})
            if not product:
                return jsonify({'error': f'Product {item["product_name"]} not found'}), 400

            variant = product['variants'][item['variant_index']]
            if variant['stock'] < item['quantity']:
                return jsonify({'error': f'Not enough stock for {item["product_name"]} ({variant["quantity"]})'}, 400)

            purchase = {
                'user_id': ObjectId(session['user_id']),
                'product_id': ObjectId(item['product_id']),
                'product_name': item['product_name'],
                'variant_index': item['variant_index'],  # Include variant_index in purchase record
                'variant_quantity': item['variant_quantity'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['price'] * item['quantity'],
                'payment_method': payment_method,
                'date': datetime.datetime.utcnow()
            }
            purchases.append(purchase)
            total_amount += purchase['total_price']

        # Process all purchases
        order_details = "Order Summary:\n\n"
        for purchase in purchases:
            # Update stock
            products_update.update_one(
                {'_id': purchase['product_id']},
                {'$inc': {f'variants.{purchase["variant_index"]}.stock': -purchase['quantity']}}
            )

            # Save purchase records
            products_sold.insert_one(purchase)
            products_by_user.insert_one(purchase)

            # Add to email details
            order_details += f"""
            Product: {purchase['product_name']}
            Quantity: {purchase['quantity']} x {purchase['variant_quantity']}
            Price per unit: ${purchase['price']}
            Subtotal: ${purchase['total_price']}
            """

        order_details += f"""
        ----------------------------------------
        Total Amount: ${total_amount}
        Payment Method: {payment_method}
        Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        """

        # Clear the cart
        session['cart'] = {}
        session.modified = True

        # Send confirmation email
        if send_purchase_confirmation_email(user['email'], user['name'], order_details):
            return jsonify({
                'success': True,
                'message': 'Purchase successful and confirmation email sent'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Purchase successful but email could not be sent'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/labor/logout')
def labor_logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('labor_panel'))

@app.route('/test-db-connection')
def test_db_connection():
    """Route to test database connectivity"""
    try:
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection not initialized'
            }), 500
        
        # Test the connection by performing a simple operation
        db.command('ping')
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to MongoDB'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(debug=True)