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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import threading
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Use environment variable for SECRET_KEY, fallback to random for development
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Custom Jinja2 filters
@app.template_filter('strftime')
def datetime_filter(date, format='%Y-%m-%d'):
    """Custom datetime filter for Jinja2 templates"""
    if date is None:
        return ''
    if isinstance(date, str):
        try:
            # Try to parse string as datetime
            date = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
        except:
            return date  # Return original string if parsing fails
    elif isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        # Convert date to datetime
        date = datetime.datetime.combine(date, datetime.time())
    
    if isinstance(date, datetime.datetime):
        return date.strftime(format)
    return str(date)

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
    # Initialize default admin user if not exists
    if db.admins.count_documents({}) == 0:
        default_admin = {
            'email': 'admin',
            'password': 'admin123',
            'name': 'Admin',
            'role': 'admin',
            'created_at': datetime.datetime.utcnow()
        }
        db.admins.insert_one(default_admin)
        print("Default admin user created")
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

def send_email(to_email, subject, html_body):
    """Send email using SMTP"""
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

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
        
        # Handle quantity conversion safely
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
worker_specific_added = db.worker_specific_added
chat_history = db.chat_history  # New collection for worker actions
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
    try:
        # Get current date for calculations
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        
        # Get statistics
        stats = {
            'total_users': users.count_documents({}),
            'new_users_today': users.count_documents({
                'created_at': {'$gte': today}
            }),
            'total_sales': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())),
            'sales_today': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
                'date': {'$gte': today}
            }))),
            'total_products': products_update.count_documents({}),
            'low_stock_products': sum(1 for product in products_update.find() 
                                    for variant in product.get('variants', []) 
                                    if isinstance(variant, dict) and variant.get('stock', 0) < 10),
            'total_workers': workers_update.count_documents({}),
            'active_workers': workers_update.count_documents({
                'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
            })
        }

        # Get recent users (for reports, not full listing)
        recent_users = list(users.find().sort('join_date', -1).limit(5))
        for user in recent_users:
            user['_id'] = str(user['_id'])

        # Get worker summary (not full listing)
        workers_summary = list(workers_update.find().limit(5))
        for worker in workers_summary:
            worker['_id'] = str(worker['_id'])

        # Get sales data for charts
        sales_data = {
            'dates': [],
            'values': []
        }
        
        # Last 7 days sales
        for i in range(6, -1, -1):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0)
            end_date = date.replace(hour=23, minute=59, second=59)
            
            daily_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
                'date': {'$gte': start_date, '$lte': end_date}
            }))
            
            sales_data['dates'].append(date.strftime('%m/%d'))
            sales_data['values'].append(daily_sales)

        # Category data for pie chart
        category_sales = {}
        for sale in products_sold.find():
            try:
                product = products_update.find_one({'_id': ObjectId(sale['product_id'])})
                if product:
                    category = product.get('category', 'Other')
                    if category not in category_sales:
                        category_sales[category] = 0
                    category_sales[category] += float(calculate_sale_amount(sale))
            except Exception as e:
                print(f"Error processing sale {sale.get('_id')}: {str(e)}")
                continue

        category_data = {
            'labels': list(category_sales.keys()) if category_sales else ['No Data'],
            'values': list(category_sales.values()) if category_sales else [0]
        }

        # Top products (for reports)
        product_sales = {}
        for sale in products_sold.find():
            try:
                product_id = sale['product_id']
                if product_id not in product_sales:
                    product = products_update.find_one({'_id': ObjectId(product_id)})
                    if product:
                        product_sales[product_id] = {
                            'name': product['name'],
                            'units_sold': 0,
                            'revenue': 0.0
                        }

                if product_id in product_sales:
                    quantity = int(extract_numeric_value(sale.get('quantity', 0)))
                    product_sales[product_id]['units_sold'] += quantity
                    
                    sale_amount = calculate_sale_amount(sale)
                    product_sales[product_id]['revenue'] += sale_amount
            except (ValueError, TypeError) as e:
                print(f"Error processing sale {sale.get('_id')}: {str(e)}")
                continue

        top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:5]

        # Product summary for reports
        total_products = products_update.count_documents({})
        total_stock_value = 0
        total_stock_quantity = 0
        
        for product in products_update.find():
            for variant in product.get('variants', []):
                if isinstance(variant, dict):
                    stock = int(variant.get('stock', 0))
                    price = float(variant.get('price', 0))
                    total_stock_quantity += stock
                    total_stock_value += stock * price

        product_summary = {
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'total_stock_quantity': total_stock_quantity,
            'low_stock_count': stats['low_stock_products']
        }

        # Ensure all numeric values in stats are proper types
        stats = {
            'total_users': int(stats['total_users']),
            'new_users_today': int(stats['new_users_today']),
            'total_sales': float(stats['total_sales']),
            'sales_today': float(stats['sales_today']),
            'total_products': int(stats['total_products']),
            'low_stock_products': int(stats['low_stock_products']),
            'total_workers': int(stats['total_workers']),
            'active_workers': int(stats['active_workers'])
        }

        return render_template('admin_dashboard.html',
                             stats=stats,
                             recent_users=recent_users,
                             workers_summary=workers_summary,
                             sales_data=sales_data,
                             category_data=category_data,
                             top_products=top_products,
                             product_summary=product_summary)

    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return render_template('admin_dashboard.html',
                             stats={'total_users': 0, 'new_users_today': 0, 'total_sales': 0.0, 
                                   'sales_today': 0.0, 'total_products': 0, 'low_stock_products': 0,
                                   'total_workers': 0, 'active_workers': 0},
                             recent_users=[],
                             workers_summary=[],
                             sales_data={'dates': [], 'values': []},
                             category_data={'labels': ['No Data'], 'values': [0]},
                             top_products=[],
                             product_summary={'total_products': 0, 'total_stock_value': 0.0, 
                                            'total_stock_quantity': 0, 'low_stock_count': 0})

# User Details View Route
@app.route('/admin/user-details/<user_id>')
@admin_required
def user_details(user_id):
    try:
        # Get user information
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        user['_id'] = str(user['_id'])
        
        # Get user's purchase history
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        total_spent = 0
        total_orders = len(user_orders)
        
        # Process orders and calculate statistics
        product_purchases = {}
        monthly_spending = {}
        
        for order in user_orders:
            order['_id'] = str(order['_id'])
            order['user_id'] = str(order['user_id'])
            order['product_id'] = str(order['product_id'])
            
            # Calculate order total
            order_total = float(calculate_sale_amount(order))
            total_spent += order_total
            order['total'] = order_total
            
            # Track product purchases
            product_id = order['product_id']
            if product_id not in product_purchases:
                product = products_update.find_one({'_id': ObjectId(product_id)})
                if product:
                    product_purchases[product_id] = {
                        'name': product['name'],
                        'quantity': 0,
                        'total_spent': 0
                    }
            
            if product_id in product_purchases:
                quantity = int(extract_numeric_value(order.get('quantity', 0)))
                product_purchases[product_id]['quantity'] += quantity
                product_purchases[product_id]['total_spent'] += order_total
            
            # Track monthly spending
            order_date = order.get('date', datetime.datetime.now())
            if isinstance(order_date, str):
                order_date = datetime.datetime.fromisoformat(order_date.replace('Z', '+00:00'))
            month_key = order_date.strftime('%Y-%m')
            
            if month_key not in monthly_spending:
                monthly_spending[month_key] = 0
            monthly_spending[month_key] += order_total
        
        # Get top purchased products
        top_products = sorted(product_purchases.values(), key=lambda x: x['total_spent'], reverse=True)[:5]
        
        # Calculate user statistics
        user_stats = {
            'total_spent': total_spent,
            'total_orders': total_orders,
            'average_order_value': total_spent / total_orders if total_orders > 0 else 0,
            'favorite_product': top_products[0]['name'] if top_products else 'None',
            'join_date': user.get('join_date', 'Unknown'),
            'last_order': max([order.get('date', datetime.datetime.min) for order in user_orders]) if user_orders else 'Never'
        }
        
        return render_template('user_detail.html', 
                             user=user, 
                             user_orders=user_orders,
                             user_stats=user_stats,
                             top_products=top_products,
                             monthly_spending=monthly_spending)
    
    except Exception as e:
        print(f"Error in user details: {e}")
        flash('Error loading user details', 'error')
        return redirect(url_for('admin_dashboard'))

# PDF Export Route
@app.route('/admin/export-user-pdf/<user_id>')
@admin_required
def export_user_pdf(user_id):
    try:
        # Get user data
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user orders
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        total_spent = sum(float(calculate_sale_amount(order)) for order in user_orders)
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"Sales Sense AI - User Report")
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # User Information
        y_position = height - 120
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "User Information")
        y_position -= 30
        
        p.setFont("Helvetica", 10)
        user_info = [
            f"Name: {user.get('name', 'N/A')}",
            f"Email: {user.get('email', 'N/A')}",
            f"Join Date: {user.get('join_date', 'N/A')}",
            f"Total Orders: {len(user_orders)}",
            f"Total Spent: ${total_spent:.2f}"
        ]
        
        for info in user_info:
            p.drawString(70, y_position, info)
            y_position -= 20
        
        # Order History
        y_position -= 20
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Recent Orders")
        y_position -= 30
        
        p.setFont("Helvetica", 8)
        headers = ["Date", "Product", "Quantity", "Price", "Total"]
        x_positions = [70, 150, 250, 320, 400]
        
        for i, header in enumerate(headers):
            p.drawString(x_positions[i], y_position, header)
        y_position -= 15
        
        for order in user_orders[:20]:  # Limit to recent 20 orders
            if y_position < 50:  # Start new page if needed
                p.showPage()
                y_position = height - 50
            
            order_date = order.get('date', datetime.datetime.now())
            if isinstance(order_date, datetime.datetime):
                date_str = order_date.strftime('%Y-%m-%d')
            else:
                date_str = str(order_date)[:10]
            
            product_name = order.get('product_name', 'Unknown')[:15]  # Truncate long names
            quantity = str(order.get('quantity', '0'))
            price = f"${float(order.get('price', 0)):.2f}"
            total = f"${float(calculate_sale_amount(order)):.2f}"
            
            row_data = [date_str, product_name, quantity, price, total]
            for i, data in enumerate(row_data):
                p.drawString(x_positions[i], y_position, str(data))
            y_position -= 15
        
        p.save()
        buffer.seek(0)
        
        from flask import Response
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=user_report_{user_id}.pdf'}
        )
    
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({'error': 'Failed to generate PDF'}), 500

# Email Marketing Route
@app.route('/admin/send-marketing-email/<user_id>')
@admin_required
def send_marketing_email(user_id):
    try:
        # Get user data
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's most purchased products
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        product_purchases = {}
        
        for order in user_orders:
            product_id = order['product_id']
            if product_id not in product_purchases:
                product_purchases[product_id] = 0
            quantity = int(extract_numeric_value(order.get('quantity', 0)))
            product_purchases[product_id] += quantity
        
        # Get top purchased product
        if product_purchases:
            top_product_id = max(product_purchases, key=product_purchases.get)
            top_product = products_update.find_one({'_id': ObjectId(top_product_id)})
            
            if top_product:
                # Create personalized email
                subject = f"Special 15% OFF on {top_product['name']} - Just for You!"
                
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #007bff;">Hi {user.get('name', 'Valued Customer')}!</h2>
                        
                        <p>We noticed you're a big fan of <strong>{top_product['name']}</strong>! 📦</p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #28a745; text-align: center;">🎉 SPECIAL OFFER JUST FOR YOU! 🎉</h3>
                            <h2 style="color: #dc3545; text-align: center; font-size: 2em;">15% OFF</h2>
                            <p style="text-align: center; font-size: 1.2em;">On your favorite product: <strong>{top_product['name']}</strong></p>
                        </div>
                        
                        <p>Since you've purchased this product <strong>{product_purchases[top_product_id]} times</strong>, we thought you'd love this exclusive discount!</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Shop Now & Save 15%</a>
                        </div>
                        
                        <p style="font-size: 0.9em; color: #666;">
                            This offer is valid for 7 days only. Don't miss out!<br>
                            Best regards,<br>
                            The Sales Sense AI Team
                        </p>
                    </div>
                </body>
                </html>
                """
                
                # Send email
                if send_email(user['email'], subject, html_body):
                    return jsonify({'success': True, 'message': f'Marketing email sent to {user["name"]}!'})
                else:
                    return jsonify({'error': 'Failed to send email'}), 500
        
        return jsonify({'error': 'No purchase history found for personalized email'}), 400
    
    except Exception as e:
        print(f"Error sending marketing email: {e}")
        return jsonify({'error': 'Failed to send marketing email'}), 500

# Chatbot functionality
@app.route('/admin/chatbot')
@admin_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/admin/chat', methods=['POST'])
@admin_required
def admin_chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower().strip()
        
        # Simple pattern matching chatbot (can be enhanced with AI later)
        response = process_admin_query(user_message)
        
        # Store chat history
        chat_history.insert_one({
            'user_type': 'admin',
            'message': user_message,
            'response': response,
            'timestamp': datetime.datetime.now()
        })
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'response': 'Sorry, I encountered an error processing your request.'})

def process_admin_query(query):
    """Process admin queries and return appropriate responses"""
    try:
        # Sales related queries
        if any(word in query for word in ['sales', 'revenue', 'money', 'earning']):
            return get_sales_summary()
        
        # User related queries
        elif any(word in query for word in ['user', 'customer', 'client']):
            return get_user_summary()
        
        # Product related queries
        elif any(word in query for word in ['product', 'inventory', 'stock']):
            return get_product_summary()
        
        # Worker related queries
        elif any(word in query for word in ['worker', 'employee', 'staff']):
            return get_worker_summary()
        
        # Top products
        elif any(word in query for word in ['top', 'best', 'popular']):
            return get_top_products_summary()
        
        # Low stock
        elif any(word in query for word in ['low stock', 'shortage', 'running out']):
            return get_low_stock_summary()
        
        # Recent activity
        elif any(word in query for word in ['recent', 'today', 'latest']):
            return get_recent_activity_summary()
        
        # General greetings
        elif any(word in query for word in ['hello', 'hi', 'hey', 'help']):
            return """Hello! I'm your Sales Sense AI assistant. I can help you with:
            
            📊 Sales data and revenue information
            👥 User and customer analytics  
            📦 Product and inventory status
            👷 Worker management information
            🏆 Top performing products
            ⚠️ Low stock alerts
            📅 Recent activity updates
            
            Just ask me anything about your business!"""
        
        else:
            return """I'm not sure about that specific query. Try asking about:
            - Sales and revenue
            - Users and customers
            - Products and inventory
            - Workers and staff
            - Top performing items
            - Stock levels
            - Recent activity"""
    
    except Exception as e:
        print(f"Error processing query: {e}")
        return "Sorry, I encountered an error processing your request."

def get_sales_summary():
    """Get sales summary for chatbot"""
    try:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        total_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())
        today_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
            'date': {'$gte': today}
        }))
        
        return f"""📊 Sales Summary:
        
💰 Total Revenue: ${total_sales:.2f}
📅 Today's Sales: ${today_sales:.2f}
📈 Growth: {((today_sales / (total_sales - today_sales)) * 100) if (total_sales - today_sales) > 0 else 0:.1f}% vs yesterday

Keep up the great work! 🚀"""
    except:
        return "Unable to fetch sales data at the moment."

def get_user_summary():
    """Get user summary for chatbot"""
    try:
        total_users = users.count_documents({})
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        new_today = users.count_documents({'created_at': {'$gte': today}})
        
        return f"""👥 User Analytics:
        
📊 Total Users: {total_users}
🆕 New Today: {new_today}
📈 Growth Rate: {(new_today / total_users * 100) if total_users > 0 else 0:.1f}%

Your user base is growing! 🎉"""
    except:
        return "Unable to fetch user data at the moment."

def get_product_summary():
    """Get product summary for chatbot"""
    try:
        total_products = products_update.count_documents({})
        low_stock = sum(1 for product in products_update.find() 
                       for variant in product.get('variants', []) 
                       if isinstance(variant, dict) and variant.get('stock', 0) < 10)
        
        return f"""📦 Inventory Status:
        
📋 Total Products: {total_products}
⚠️ Low Stock Items: {low_stock}
✅ Well Stocked: {total_products - low_stock}

{f'⚠️ Attention needed for {low_stock} items!' if low_stock > 0 else '✅ All products well stocked!'}"""
    except:
        return "Unable to fetch product data at the moment."

def get_worker_summary():
    """Get worker summary for chatbot"""
    try:
        total_workers = workers_update.count_documents({})
        active_workers = workers_update.count_documents({
            'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
        })
        
        return f"""👷 Workforce Overview:
        
👥 Total Workers: {total_workers}
🟢 Active Today: {active_workers}
📊 Activity Rate: {(active_workers / total_workers * 100) if total_workers > 0 else 0:.1f}%

Your team is doing great! 💪"""
    except:
        return "Unable to fetch worker data at the moment."

def get_top_products_summary():
    """Get top products summary for chatbot"""
    try:
        product_sales = {}
        for sale in products_sold.find():
            product_id = sale['product_id']
            if product_id not in product_sales:
                product = products_update.find_one({'_id': ObjectId(product_id)})
                if product:
                    product_sales[product_id] = {
                        'name': product['name'],
                        'revenue': 0
                    }
            
            if product_id in product_sales:
                product_sales[product_id]['revenue'] += float(calculate_sale_amount(sale))
        
        top_3 = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:3]
        
        response = "🏆 Top Performing Products:\n\n"
        for i, product in enumerate(top_3, 1):
            response += f"{i}. {product['name']} - ${product['revenue']:.2f}\n"
        
        return response + "\nThese are your bestsellers! 🌟"
    except:
        return "Unable to fetch top products data at the moment."

def get_low_stock_summary():
    """Get low stock summary for chatbot"""
    try:
        low_stock_items = []
        for product in products_update.find():
            for variant in product.get('variants', []):
                if isinstance(variant, dict) and variant.get('stock', 0) < 10:
                    low_stock_items.append({
                        'name': product['name'],
                        'variant': variant.get('size', 'Default'),
                        'stock': variant.get('stock', 0)
                    })
        
        if low_stock_items:
            response = "⚠️ Low Stock Alert:\n\n"
            for item in low_stock_items[:5]:  # Show top 5
                response += f"• {item['name']} ({item['variant']}) - {item['stock']} left\n"
            
            return response + f"\n📦 {len(low_stock_items)} items need restocking!"
        else:
            return "✅ Great news! All products are well stocked. No immediate restocking needed."
    except:
        return "Unable to fetch stock data at the moment."

def get_recent_activity_summary():
    """Get recent activity summary for chatbot"""
    try:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        
        new_users = users.count_documents({'created_at': {'$gte': today}})
        today_sales = list(products_sold.find({'date': {'$gte': today}}))
        today_revenue = sum(float(calculate_sale_amount(sale)) for sale in today_sales)
        
        return f"""📅 Today's Activity:
        
🆕 New Registrations: {new_users}
🛒 Orders Placed: {len(today_sales)}
💰 Revenue Generated: ${today_revenue:.2f}

{f'🎉 Busy day ahead!' if len(today_sales) > 5 else '📈 Steady progress!'}"""
    except:
        return "Unable to fetch recent activity data at the moment."

# Auto-refresh functionality
auto_refresh_cache = {}
cache_lock = threading.Lock()

def refresh_data_cache():
    """Background function to refresh data cache every 15 minutes"""
    while True:
        try:
            with cache_lock:
                print("Refreshing data cache...")
                
                # Cache statistics
                auto_refresh_cache['stats'] = {
                    'total_users': users.count_documents({}),
                    'total_sales': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())),
                    'total_products': products_update.count_documents({}),
                    'total_workers': workers_update.count_documents({})
                }
                
                auto_refresh_cache['last_updated'] = datetime.datetime.now()
                print("Data cache refreshed successfully")
                
        except Exception as e:
            print(f"Error refreshing cache: {e}")
        
        # Wait 15 minutes (900 seconds)
        time.sleep(900)

def start_auto_refresh_thread():
    """Start the auto-refresh background thread"""
    refresh_thread = threading.Thread(target=refresh_data_cache, daemon=True)
    refresh_thread.start()
    print("Auto-refresh thread started")

@app.route('/admin/cache-status')
@admin_required
def cache_status():
    """Get cache status for debugging"""
    with cache_lock:
        return jsonify({
            'cache_size': len(auto_refresh_cache),
            'last_updated': auto_refresh_cache.get('last_updated'),
            'stats': auto_refresh_cache.get('stats', {})
        })

# API endpoint for business stats (for home page)
@app.route('/api/business-stats')
def business_stats_api():
    try:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        
        stats = {
            'total_users': users.count_documents({}),
            'new_users_today': users.count_documents({'created_at': {'$gte': today}}),
            'total_sales': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())),
            'sales_today': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
                'date': {'$gte': today}
            }))),
            'total_products': products_update.count_documents({}),
            'total_workers': workers_update.count_documents({})
        }
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting business stats: {e}")
        return jsonify({
            'total_users': 0,
            'new_users_today': 0,
            'total_sales': 0.0,
            'sales_today': 0.0,
            'total_products': 0,
            'total_workers': 0
        })

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
                return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error creating worker: {str(e)}', 'error')
            return redirect(url_for('admin_panel'))

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
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic input validation
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('admin_login.html')
        
        try:
            # Check database connection first
            if db is None:
                flash('Database connection error. Please contact administrator.', 'error')
                return render_template('admin_login.html')
            
            # Check for default admin credentials (both 'admin' and 'admin@salessense.com')
            if (email in ['admin', 'admin@salessense.com'] and password == 'admin123'):
                # Try to find existing admin user
                admin = admins.find_one({'$or': [{'email': 'admin'}, {'email': 'admin@salessense.com'}]})
                
                if not admin:
                    # Create admin user if it doesn't exist
                    admin = {
                        'email': 'admin@salessense.com',
                        'password': 'admin123',
                        'name': 'Admin',
                        'role': 'admin',
                        'created_at': datetime.datetime.utcnow()
                    }
                    result = admins.insert_one(admin)
                    session['admin_id'] = str(result.inserted_id)
                    print("Created new admin user")
                else:
                    session['admin_id'] = str(admin['_id'])
                    print("Found existing admin user")
                
                session['admin_name'] = 'Admin'
                session['admin_logged_in'] = True
                session['login_time'] = datetime.datetime.utcnow().timestamp()
                session['last_activity'] = datetime.datetime.utcnow().timestamp()
                
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                # Check for other admin users in database
                admin = admins.find_one({'email': email, 'password': password})
                if admin:
                    session['admin_id'] = str(admin['_id'])
                    session['admin_name'] = admin.get('name', 'Admin')
                    session['admin_logged_in'] = True
                    session['login_time'] = datetime.datetime.utcnow().timestamp()
                    session['last_activity'] = datetime.datetime.utcnow().timestamp()
                    
                    flash('Login successful!', 'success')
                    return redirect(url_for('admin_dashboard'))
                
            flash('Invalid credentials. Use admin/admin123 for default login.', 'error')
            
        except Exception as e:
            print(f"Admin login error: {e}")
            flash(f'Login error: {str(e)}', 'error')
            
        return render_template('admin_login.html')
    
    return render_template('admin_login.html')

@app.route('/admin/debug')
def admin_debug():
    """Debug route to check admin setup"""
    try:
        if db is None:
            return jsonify({'error': 'Database not connected'})
        
        # Check admin users
        admin_count = admins.count_documents({})
        admin_users = list(admins.find({}, {'password': 0}))  # Don't return passwords
        
        return jsonify({
            'database_connected': True,
            'admin_count': admin_count,
            'admin_users': admin_users,
            'collections': db.list_collection_names()
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database_connected': False})



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
    # Start auto-refresh background thread
    start_auto_refresh_thread()
    # Use environment variable for port (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)