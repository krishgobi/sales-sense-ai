from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, make_response
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

# ===== INTELLIGENT ADMIN NOTIFICATION SYSTEM =====

# Indian Festivals Configuration with Product Recommendations
INDIAN_FESTIVALS = {
    'Pongal': {
        'month': 'January',
        'products': ['Rice', 'Milk', 'Coconut', 'Jaggery'],
        'categories': ['Food & Beverages', 'Traditional Foods'],
        'discount_range': '10-25%',
        'boost_percentage': 40
    },
    'Holi': {
        'month': 'March', 
        'products': ['Sweets', 'Colors', 'Snacks', 'Traditional Sweets'],
        'categories': ['Food & Beverages', 'Festival Items'],
        'discount_range': '15-30%',
        'boost_percentage': 35
    },
    'Diwali': {
        'month': 'October',
        'products': ['Sweets', 'Nuts', 'Lamps', 'Traditional Sweets', 'Dry Fruits'],
        'categories': ['Food & Beverages', 'Festival Items', 'Traditional Foods'],
        'discount_range': '20-40%',
        'boost_percentage': 50
    },
    'Christmas': {
        'month': 'December',
        'products': ['Cake', 'Chocolate', 'Wine', 'Gifts', 'Plum Cake'],
        'categories': ['Food & Beverages', 'Gifts & Occasions'],
        'discount_range': '15-35%',
        'boost_percentage': 30
    },
    'New Year': {
        'month': 'January',
        'products': ['Party Snacks', 'Beverages', 'Champagne', 'Cake'],
        'categories': ['Food & Beverages', 'Party Supplies'],
        'discount_range': '20-30%',
        'boost_percentage': 25
    },
    'Ganesh Chaturthi': {
        'month': 'August',
        'products': ['Modak', 'Fruits', 'Flowers', 'Traditional Sweets'],
        'categories': ['Food & Beverages', 'Festival Items', 'Traditional Foods'],
        'discount_range': '15-25%',
        'boost_percentage': 35
    }
}

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
    
    # Create indexes for faster queries
    print("Creating database indexes...")
    try:
        # Compound indexes for common query patterns
        db.products_sold.create_index([('date', -1), ('total', 1)])
        db.products_sold.create_index([('date', -1), ('product_id', 1)])
        db.products_sold.create_index([('date', -1), ('user_id', 1)])
        db.products_sold.create_index([('product_id', 1)])
        db.products_sold.create_index([('user_id', 1)])
        
        # User indexes
        db.users.create_index([('email', 1)], unique=True)
        db.users.create_index([('created_at', -1)])
        db.users.create_index([('last_purchase', -1)])
        
        # Product indexes
        db.products_update.create_index([('category', 1)])
        db.products_update.create_index([('name', 1)])
        
        print("Database indexes created successfully")
    except Exception as idx_error:
        print(f"Index creation warning: {idx_error}")
    
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

# ===== INTELLIGENT NOTIFICATION FUNCTIONS =====

def get_upcoming_festivals():
    """Get festivals in the next 2 months"""
    current_month = datetime.datetime.now().month
    next_month = (current_month % 12) + 1
    
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August', 
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    upcoming = []
    for festival, data in INDIAN_FESTIVALS.items():
        festival_month = data['month']
        current_month_name = month_names.get(current_month, '')
        next_month_name = month_names.get(next_month, '')
        
        if festival_month in [current_month_name, next_month_name]:
            upcoming.append({
                'name': festival,
                'month': festival_month,
                'recommended_products': data['products'],
                'categories': data['categories'],
                'discount_range': data['discount_range']
            })
    
    return upcoming

def analyze_product_performance():
    """Analyze product performance over the last 3 months"""
    try:
        if db is None:
            return {'top_performers': [], 'poor_performers': [], 'error': 'Database not connected'}
        
        three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)
        
        # First, let's get all sales data from the last 3 months
        sales_data = list(db.products_sold.find({
            'date': {'$gte': three_months_ago}
        }))
        
        print(f"Found {len(sales_data)} sales records in last 90 days")
        
        if not sales_data:
            # If no recent data, use all available data
            sales_data = list(db.products_sold.find({}).limit(100))  # Get some data for analysis
            print(f"No recent sales, using {len(sales_data)} historical records")
        
        if not sales_data:
            return {'top_performers': [], 'poor_performers': [], 'error': 'No sales data found'}
        
        # Group sales by product
        product_stats = {}
        for sale in sales_data:
            product_id = str(sale.get('product_id', ''))
            if not product_id:
                continue
                
            if product_id not in product_stats:
                product_stats[product_id] = {
                    'total_revenue': 0,
                    'total_quantity': 0,
                    'customers': set(),
                    'order_count': 0
                }
            
            # Add sale data
            product_stats[product_id]['total_revenue'] += float(sale.get('total', 0))
            product_stats[product_id]['total_quantity'] += int(sale.get('quantity', 0))
            product_stats[product_id]['customers'].add(str(sale.get('user_id', '')))
            product_stats[product_id]['order_count'] += 1
        
        # Get product details and create final results
        results = []
        for product_id, stats in product_stats.items():
            try:
                # Get product info
                if len(product_id) == 24:  # ObjectId length
                    product_info = db.products_update.find_one({'_id': ObjectId(product_id)})
                else:
                    product_info = db.products_update.find_one({'_id': product_id})
                
                if not product_info:
                    continue
                
                customer_count = len(stats['customers'])
                
                results.append({
                    'product_id': product_id,
                    'name': product_info.get('name', 'Unknown Product'),
                    'category': product_info.get('category', 'Unknown'),
                    'revenue': stats['total_revenue'],
                    'quantity_sold': stats['total_quantity'],
                    'customer_count': customer_count,
                    'order_count': stats['order_count'],
                    'avg_order_value': stats['total_revenue'] / stats['order_count'] if stats['order_count'] > 0 else 0
                })
            except Exception as e:
                print(f"Error processing product {product_id}: {e}")
                continue
        
        if not results:
            return {'top_performers': [], 'poor_performers': [], 'error': 'No valid product data found'}
        
        # Sort by customer engagement (customer count is priority, then revenue)
        results.sort(key=lambda x: (x['customer_count'], x['revenue']), reverse=True)
        
        print(f"Analyzed {len(results)} products")
        
        # Calculate performance thresholds
        total_products = len(results)
        top_20_percent = max(1, total_products // 5)
        bottom_20_percent = max(1, total_products // 5)
        
        # Identify high performers (top 20% by customer engagement)
        top_performers = results[:top_20_percent]
        for product in top_performers:
            if product['customer_count'] >= 3:  # Lower threshold for more results
                recommended_increase = 30 + (product['customer_count'] * 2)
                recommended_increase = min(recommended_increase, 50)
                product['action'] = f"Increase stock by {recommended_increase}% - High demand product"
            else:
                product['action'] = "Monitor closely - Growing popularity"
        
        # Identify poor performers (bottom 20% by customer engagement and revenue)
        poor_performers = results[-bottom_20_percent:]
        for product in poor_performers:
            if product['customer_count'] <= 1 and product['revenue'] < 50:
                product['action'] = "Consider reducing stock by 50% - Low demand"
            elif product['customer_count'] <= 1:
                product['action'] = "Reduce stock by 30% and consider promotion"
            else:
                product['action'] = "Review pricing strategy"
        
        print(f"Top performers: {len(top_performers)}, Poor performers: {len(poor_performers)}")
        
        return {
            'top_performers': top_performers,
            'poor_performers': poor_performers,
            'analysis_period': '90 days',
            'total_products_analyzed': total_products
        }
        
    except Exception as e:
        print(f"Error in product performance analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            'top_performers': [],
            'poor_performers': [],
            'error': str(e),
            'analysis_period': '90 days',
            'total_products_analyzed': 0
        }

def generate_festival_recommendations():
    """Generate festival-specific product recommendations"""
    recommendations = []
    upcoming_festivals = get_upcoming_festivals()
    
    try:
        # Get current product inventory status
        products = list(db.products_update.find({}, {'name': 1, 'category': 1, 'price': 1}))
        
        for festival in upcoming_festivals:
            festival_name = festival['name']
            recommended_products = festival['recommended_products']
            
            # Find matching products in inventory
            matching_products = []
            for product in products:
                product_name = product['name'].lower()
                for rec_product in recommended_products:
                    if rec_product.lower() in product_name:
                        matching_products.append(product['name'])
                        break
            
            if matching_products:
                recommendation = {
                    'festival': festival_name,
                    'message': f"Prepare for {festival_name} ({festival['month']}) - Stock up on: {', '.join(matching_products[:3])}. Suggested discount: {festival['discount_range']}",
                    'products': matching_products,
                    'discount_range': festival['discount_range'],
                    'priority': 'high' if festival['month'] == datetime.datetime.now().strftime('%B') else 'medium'
                }
                recommendations.append(recommendation)
    
    except Exception as e:
        print(f"Error generating festival recommendations: {e}")
    
    return recommendations

def get_admin_notifications():
    """Get all intelligent admin notifications"""
    notifications = []
    
    try:
        # Product performance notifications
        performance_data = analyze_product_performance()
        
        # High performers notifications
        for product in performance_data['top_performers'][:5]:  # Top 5
            notifications.append({
                'type': 'high_performer',
                'priority': 'high',
                'message': f"🔥 '{product['name']}' is trending! {product['customer_count']} customers bought this product.",
                'recommendation': product['action'],
                'product': product['name']
            })
        
        # Poor performers notifications  
        for product in performance_data['poor_performers'][:3]:  # Bottom 3
            notifications.append({
                'type': 'poor_performer',
                'priority': 'medium',
                'message': f"⚠️ '{product['name']}' has low demand. Only {product['customer_count']} customers interested.",
                'recommendation': product['action'],
                'product': product['name']
            })
        
        # Festival recommendations
        festival_recs = generate_festival_recommendations()
        for rec in festival_recs:
            notifications.append({
                'type': 'festival_recommendation',
                'priority': rec['priority'],
                'message': f"🎉 {rec['message']}",
                'recommendation': f"Prepare inventory and marketing for {rec['festival']}",
                'festival': rec['festival']
            })
        
        # Inventory alerts based on recent sales trends
        notifications.extend(get_inventory_alerts())
        
    except Exception as e:
        print(f"Error getting admin notifications: {e}")
    
    return {'notifications': notifications, 'count': len(notifications)}

def get_inventory_alerts():
    """Generate inventory management alerts"""
    alerts = []
    
    try:
        # Check for products with sudden sales spikes
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        
        recent_pipeline = [
            {'$match': {'date': {'$gte': seven_days_ago}}},
            {'$group': {
                '_id': '$product_id',
                'recent_sales': {'$sum': '$quantity'},
                'recent_revenue': {'$sum': '$total'}
            }}
        ]
        
        historical_pipeline = [
            {'$match': {'date': {'$gte': thirty_days_ago, '$lt': seven_days_ago}}},
            {'$group': {
                '_id': '$product_id',
                'historical_sales': {'$sum': '$quantity'},
                'historical_revenue': {'$sum': '$total'}
            }}
        ]
        
        recent_data = {item['_id']: item for item in db.products_sold.aggregate(recent_pipeline)}
        historical_data = {item['_id']: item for item in db.products_sold.aggregate(historical_pipeline)}
        
        # Detect sudden spikes
        for product_id, recent in recent_data.items():
            historical = historical_data.get(product_id, {'historical_sales': 0})
            
            # Calculate weekly average from historical data
            weekly_avg = historical['historical_sales'] / 3 if historical['historical_sales'] > 0 else 0
            
            # If recent sales are significantly higher than average
            if weekly_avg > 0 and recent['recent_sales'] > weekly_avg * 2:
                try:
                    product_info = db.products_update.find_one({'_id': ObjectId(product_id)})
                    if product_info:
                        alerts.append({
                            'type': 'sales_spike',
                            'priority': 'high',
                            'message': f"📈 Sales spike detected for '{product_info['name']}' - {recent['recent_sales']} units this week vs {weekly_avg:.1f} weekly average",
                            'recommendation': f"Consider increasing stock by 40% for '{product_info['name']}' due to high demand",
                            'product': product_info['name']
                        })
                except:
                    pass
    
    except Exception as e:
        print(f"Error in inventory alerts: {e}")
    
    return alerts

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

# Collections - Only initialize if db connection exists
if db is not None:
    products_update = db.products_update
    workers_update = db.workers_update  # Changed from workers to workers_update
    worker_specific_added = db.worker_specific_added
    chat_history = db.chat_history  # New collection for worker actions
    labors = db.labors
    admins = db.admins
    users = db.users  # FIXED: Using correct users collection with 1750 users
    products_sold = db.products_sold
    products_by_user = db.products_by_user
else:
    # Set collections to None if database connection failed
    products_update = None
    workers_update = None
    worker_specific_added = None
    chat_history = None
    labors = None
    admins = None
    users = None
    products_sold = None
    products_by_user = None

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
    
    # Parse variants if they're stored as strings
    import ast
    for product in all_products:
        if 'variants' in product and isinstance(product['variants'], str):
            try:
                product['variants'] = ast.literal_eval(product['variants'])
            except:
                product['variants'] = []
    
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
    # Refactored to use shared dashboard builder
    try:
        ctx = build_dashboard_context()
        print(f"🔍 DEBUG: Dashboard Context - Total Users: {ctx.get('pagination', {}).get('total', 0)}, Recent Users Count: {len(ctx.get('recent_users', []))}")
        response = make_response(render_template('admin_dashboard.html', **ctx))
        # Add cache control headers to prevent browser caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error rendering admin dashboard: {e}")
        # Fallback minimal render
        response = make_response(render_template('admin_dashboard.html',
                             stats={'total_users': 0, 'new_users_today': 0, 'total_sales': 0.0,
                                   'sales_today': 0.0, 'total_products': 0, 'low_stock_products': 0,
                                   'total_workers': 0, 'active_workers': 0},
                             recent_users=[],
                             workers_summary=[],
                             sales_data={'dates': [], 'values': []},
                             category_data={'labels': ['No Data'], 'values': [0]},
                             top_products=[],
                             product_summary={'total_products': 0, 'total_stock_value': 0.0,
                                            'total_stock_quantity': 0, 'low_stock_count': 0}))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response


def build_dashboard_context():
    """Build and return the context dict used by the admin dashboard.
    This is factored out so we can expose a public demo dashboard safely.
    """
    try:
        # Get current date for calculations
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)

        # Use MongoDB aggregation for faster total sales calculation
        total_sales_pipeline = [
            {'$group': {
                '_id': None,
                'total': {'$sum': '$total'}
            }}
        ]
        total_sales_result = list(products_sold.aggregate(total_sales_pipeline))
        total_sales = float(total_sales_result[0]['total']) if total_sales_result else 0.0

        # Calculate today's sales using aggregation
        sales_today_pipeline = [
            {'$match': {'date': {'$gte': today}}},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$total'}
            }}
        ]
        sales_today_result = list(products_sold.aggregate(sales_today_pipeline))
        sales_today = float(sales_today_result[0]['total']) if sales_today_result else 0.0

        # Get statistics - optimized queries
        stats = {
            'total_users': users.count_documents({}) if users is not None else 0,
            'new_users_today': users.count_documents({'created_at': {'$gte': today}}) if users is not None else 0,
            'total_sales': total_sales,
            'sales_today': sales_today,
            'total_products': products_update.count_documents({}) if products_update is not None else 0,
            'low_stock_products': 0,  # Will calculate separately
            'total_workers': workers_update.count_documents({}) if workers_update is not None else 0,
            'active_workers': workers_update.count_documents({'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}}) if workers_update is not None else 0
        }

        # Calculate low stock products efficiently
        low_stock_count = 0
        if products_update is not None:
            for product in products_update.find({}, {'variants': 1}):
                for variant in product.get('variants', []):
                    if isinstance(variant, dict) and variant.get('stock', 0) < 10:
                        low_stock_count += 1
        stats['low_stock_products'] = low_stock_count

        # Get recent users with pagination support
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Show 20 users per page
        skip = (page - 1) * per_page

        total_users_count = users.count_documents({}) if users is not None else 0
        total_pages = (total_users_count + per_page - 1) // per_page if total_users_count else 0

        recent_users = []
        if users is not None:
            recent_users = list(users.find().sort('created_at', -1).skip(skip).limit(per_page))
            for user in recent_users:
                user['_id'] = str(user['_id'])

        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_users_count,
            'pages': total_pages
        }

        # Get worker summary (not full listing)
        workers_summary = []
        if workers_update is not None:
            workers_summary = list(workers_update.find().limit(5))
            for worker in workers_summary:
                worker['_id'] = str(worker['_id'])

        # Get sales data for charts - using aggregation for speed
        sales_data = {
            'dates': [],
            'values': []
        }

        # Last 7 days sales using aggregation
        for i in range(6, -1, -1):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0)
            end_date = date.replace(hour=23, minute=59, second=59)

            # Use aggregation for faster calculation
            daily_sales_pipeline = [
                {'$match': {'date': {'$gte': start_date, '$lte': end_date}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
            ]
            daily_result = list(products_sold.aggregate(daily_sales_pipeline)) if products_sold is not None else []
            daily_sales = float(daily_result[0]['total']) if daily_result else 0.0

            sales_data['dates'].append(date.strftime('%m/%d'))
            sales_data['values'].append(daily_sales)

        # Category data for pie chart - using aggregation with lookup
        category_sales_pipeline = [
            {'$lookup': {
                'from': 'products_update',
                'localField': 'product_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
            {'$group': {
                '_id': {'$ifNull': ['$product.category', 'Other']},
                'total': {'$sum': '$total'}
            }}
        ]

        category_sales = {}
        try:
            category_results = list(products_sold.aggregate(category_sales_pipeline)) if products_sold is not None else []
            for result in category_results:
                category_sales[result['_id']] = float(result['total'])
        except Exception as e:
            print(f"Error in category aggregation: {str(e)}")
            # Fallback to simpler method
            category_sales = {'Other': total_sales}

        category_data = {
            'labels': list(category_sales.keys()) if category_sales else ['No Data'],
            'values': list(category_sales.values()) if category_sales else [0]
        }

        # Top products (for reports) - using aggregation
        top_products_pipeline = [
            {'$group': {
                '_id': '$product_id',
                'total_revenue': {'$sum': '$total'},
                'units_sold': {'$sum': '$quantity'},
                'product_name': {'$first': '$product_name'}
            }},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 5}
        ]

        top_products = []
        try:
            top_products_results = list(products_sold.aggregate(top_products_pipeline)) if products_sold is not None else []
            for result in top_products_results:
                top_products.append({
                    'name': result.get('product_name', 'Unknown'),
                    'units_sold': int(result.get('units_sold', 0)),
                    'revenue': float(result.get('total_revenue', 0.0))
                })
        except Exception as e:
            print(f"Error in top products aggregation: {str(e)}")
            top_products = []

        # Product summary for reports
        total_products = products_update.count_documents({}) if products_update is not None else 0
        total_stock_value = 0
        total_stock_quantity = 0

        if products_update is not None:
            for product in products_update.find():
                for variant in product.get('variants', []):
                    if isinstance(variant, dict):
                        stock = int(variant.get('stock', 0))
                        # Cap display stock at 1024 for better readability
                        stock = min(stock, 1024)
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

        return {
            'stats': stats,
            'recent_users': recent_users,
            'pagination': pagination,
            'workers_summary': workers_summary,
            'sales_data': sales_data,
            'category_data': category_data,
            'top_products': top_products,
            'product_summary': product_summary
        }

    except Exception as e:
        print(f"Error building dashboard context: {e}")
        return {
            'stats': {'total_users': 0, 'new_users_today': 0, 'total_sales': 0.0, 'sales_today': 0.0, 'total_products': 0, 'low_stock_products': 0, 'total_workers': 0, 'active_workers': 0},
            'recent_users': [],
            'pagination': {'page': 1, 'per_page': 20, 'total': 0, 'pages': 0},
            'workers_summary': [],
            'sales_data': {'dates': [], 'values': []},
            'category_data': {'labels': ['No Data'], 'values': [0]},
            'top_products': [],
            'product_summary': {'total_products': 0, 'total_stock_value': 0.0, 'total_stock_quantity': 0, 'low_stock_count': 0}
        }


@app.route('/demo-dashboard')
@require_db_connection
def demo_dashboard():
    """Public demo dashboard showing the same analytics without login."""
    try:
        ctx = build_dashboard_context()
        # Inform template this is demo/public mode so it can hide admin actions
        ctx['demo_mode'] = True
        return render_template('admin_dashboard.html', **ctx)
    except Exception as e:
        print(f"Error rendering demo dashboard: {e}")
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
        
        # Use aggregation for faster calculations - handle null totals
        total_sales_pipeline = [
            {'$match': {'total': {'$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        total_sales_result = list(products_sold.aggregate(total_sales_pipeline))
        total_sales = float(total_sales_result[0]['total']) if total_sales_result and total_sales_result[0].get('total') else 0.0
        
        sales_today_pipeline = [
            {'$match': {'date': {'$gte': today}, 'total': {'$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        sales_today_result = list(products_sold.aggregate(sales_today_pipeline))
        sales_today = float(sales_today_result[0]['total']) if sales_today_result and sales_today_result[0].get('total') else 0.0
        
        # Get total sales count
        total_orders = products_sold.count_documents({'total': {'$ne': None}})
        orders_today = products_sold.count_documents({'date': {'$gte': today}, 'total': {'$ne': None}})
        
        # Get active users (purchased in last 30 days) - check last_purchase exists and is not None
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        active_users = users.count_documents({
            'last_purchase': {'$exists': True, '$ne': None, '$gte': thirty_days_ago}
        })
        
        # Get top selling products (last 30 days)
        top_products_pipeline = [
            {'$match': {'date': {'$gte': thirty_days_ago}, 'total': {'$ne': None}}},
            {'$group': {
                '_id': '$product_name',
                'total_revenue': {'$sum': '$total'},
                'units_sold': {'$sum': '$quantity'}
            }},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 5}
        ]
        top_products_result = list(products_sold.aggregate(top_products_pipeline))
        top_products = [
            {
                'name': p['_id'],
                'revenue': float(p.get('total_revenue', 0)),
                'units': int(p.get('units_sold', 0))
            }
            for p in top_products_result
        ]
        
        # Last 7 days sales trend
        sales_trend = []
        for i in range(6, -1, -1):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            start = date.replace(hour=0, minute=0, second=0)
            end = date.replace(hour=23, minute=59, second=59)
            
            daily_pipeline = [
                {'$match': {'date': {'$gte': start, '$lte': end}, 'total': {'$ne': None}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
            ]
            daily_result = list(products_sold.aggregate(daily_pipeline))
            daily_sales = float(daily_result[0]['total']) if daily_result and daily_result[0].get('total') else 0.0
            
            sales_trend.append({
                'date': date.strftime('%m/%d'),
                'sales': daily_sales
            })
        
        stats = {
            'total_users': users.count_documents({}),
            'new_users_today': users.count_documents({'created_at': {'$gte': today}}),
            'active_users': active_users,
            'total_sales': total_sales,
            'sales_today': sales_today,
            'total_orders': total_orders,
            'orders_today': orders_today,
            'total_products': products_update.count_documents({}),
            'total_workers': workers_update.count_documents({}),
            'top_products': top_products,
            'sales_trend': sales_trend,
            'avg_order_value': round(total_sales / total_orders, 2) if total_orders > 0 else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting business stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'total_users': 0,
            'new_users_today': 0,
            'active_users': 0,
            'total_sales': 0.0,
            'sales_today': 0.0,
            'total_orders': 0,
            'orders_today': 0,
            'total_products': 0,
            'total_workers': 0,
            'top_products': [],
            'sales_trend': [],
            'avg_order_value': 0
        })

@app.route('/api/notifications')
def public_notifications_api():
    """Get intelligent notifications for home page (public access)"""
    try:
        notifications_data = get_admin_notifications()
        return jsonify(notifications_data)
    except Exception as e:
        print(f"Error in public notifications API: {e}")
        return jsonify({'error': str(e), 'notifications': []}), 500

@app.route('/api/product-insights')
def public_product_insights():
    """Get product performance insights for home page (public access)"""
    try:
        performance_data = analyze_product_performance()
        return jsonify(performance_data)
    except Exception as e:
        print(f"Error in public product insights API: {e}")
        return jsonify({'error': str(e), 'top_performers': [], 'poor_performers': []}), 500

@app.route('/api/festival-calendar')
def public_festival_calendar():
    """Get festival calendar for home page (public access)"""
    try:
        festivals = get_upcoming_festivals()
        recommendations = generate_festival_recommendations()
        
        return jsonify({
            'upcoming_festivals': festivals,
            'recommendations': recommendations,
            'current_month': datetime.datetime.now().month,
            'festival_config': INDIAN_FESTIVALS
        })
    except Exception as e:
        print(f"Error in public festival calendar API: {e}")
        return jsonify({
            'error': str(e), 
            'upcoming_festivals': [], 
            'recommendations': [], 
            'current_month': datetime.datetime.now().month
        }), 500

@app.route('/api/products-list')
def products_list_api():
    """Get list of all products for filter dropdown"""
    try:
        products = list(products_update.find({}, {'_id': 1, 'name': 1, 'category': 1}))
        for p in products:
            p['_id'] = str(p['_id'])
        return jsonify(products)
    except Exception as e:
        print(f"Error getting products list: {e}")
        return jsonify([])

@app.route('/api/users-list')
def users_list_api():
    """Get list of all users for filter dropdown"""
    try:
        users_list = list(users.find({}, {'_id': 1, 'name': 1, 'email': 1}).sort('name', 1))
        for u in users_list:
            u['_id'] = str(u['_id'])
        return jsonify(users_list)
    except Exception as e:
        print(f"Error getting users list: {e}")
        return jsonify([])

@app.route('/api/analytics')
def analytics_api():
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date') or request.args.get('start')
        end_date_str = request.args.get('end_date') or request.args.get('end')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Get optional filters
        products_filter = request.args.get('products', '')
        users_filter = request.args.get('users', '')
        
        # Build base match query
        base_match = {
            'date': {'$gte': start_date, '$lte': end_date},
            'total': {'$ne': None}
        }
        
        # Add product filter if specified
        if products_filter:
            product_ids = products_filter.split(',')
            base_match['product_id'] = {'$in': product_ids}
        
        # Add user filter if specified
        if users_filter:
            user_ids = users_filter.split(',')
            base_match['user_id'] = {'$in': user_ids}
        
        # Sales in period (using filtered match)
        period_sales_pipeline = [
            {'$match': base_match},
            {'$group': {
                '_id': None,
                'total_revenue': {'$sum': '$total'},
                'total_orders': {'$sum': 1},
                'total_units': {'$sum': '$quantity'}
            }}
        ]
        period_sales_result = list(products_sold.aggregate(period_sales_pipeline, allowDiskUse=True))
        
        if period_sales_result:
            total_revenue = float(period_sales_result[0]['total_revenue'])
            total_orders = int(period_sales_result[0]['total_orders'])
            total_units = int(period_sales_result[0]['total_units'])
            avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0
        else:
            total_revenue = 0
            total_orders = 0
            total_units = 0
            avg_order_value = 0
        
        # Active customers in period (made purchases) - with filters
        active_customers_pipeline = [
            {'$match': base_match},
            {'$group': {'_id': '$user_id'}}
        ]
        active_customers = len(list(products_sold.aggregate(active_customers_pipeline, allowDiskUse=True)))
        
        # New customers in period - with user filter if specified
        new_customers_query = {'created_at': {'$gte': start_date, '$lte': end_date}}
        if users_filter:
            user_object_ids = [ObjectId(uid) for uid in users_filter.split(',') if uid]
            new_customers_query['_id'] = {'$in': user_object_ids}
        new_customers = users.count_documents(new_customers_query)
        
        # Top products in period (with filters)
        top_products_pipeline = [
            {'$match': base_match},
            {'$group': {
                '_id': '$product_name',
                'total_revenue': {'$sum': '$total'},
                'units_sold': {'$sum': '$quantity'}
            }},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 10}
        ]
        top_products_result = list(products_sold.aggregate(top_products_pipeline, allowDiskUse=True))
        top_products = [
            {
                'name': p['_id'],
                'revenue': float(p['total_revenue']),
                'units': int(p['units_sold'])
            }
            for p in top_products_result
        ]
        
        # All products performance (with filters) - Optimized with lookup and ObjectId conversion
        all_products_pipeline = [
            {'$match': base_match},
            {'$group': {
                '_id': '$product_id',
                'product_name': {'$first': '$product_name'},
                'total_revenue': {'$sum': '$total'},
                'units_sold': {'$sum': '$quantity'}
            }},
            {'$addFields': {
                'product_object_id': {'$toObjectId': '$_id'}
            }},
            {'$lookup': {
                'from': 'products_update',
                'localField': 'product_object_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
            {'$addFields': {
                'category': {'$ifNull': ['$product.category', 'Other']},
                'variants': {'$ifNull': ['$product.variants', []]}
            }},
            {'$sort': {'total_revenue': -1}}
        ]
        all_products_result = list(products_sold.aggregate(all_products_pipeline, allowDiskUse=True))
        
        all_products = []
        for p in all_products_result:
            total_stock = 0
            for variant in p.get('variants', []):
                if isinstance(variant, dict):
                    total_stock += int(variant.get('stock', 0))
            
            all_products.append({
                'name': p.get('product_name', 'Unknown'),
                'category': p.get('category', 'Other'),
                'revenue': float(p.get('total_revenue', 0)),
                'units_sold': int(p.get('units_sold', 0)),
                'stock': total_stock
            })
        
        # Category sales (with filters) - Optimized with aggregation
        category_sales_pipeline = [
            {'$match': base_match},
            {'$addFields': {
                'product_object_id': {'$toObjectId': '$product_id'}
            }},
            {'$lookup': {
                'from': 'products_update',
                'localField': 'product_object_id',
                'foreignField': '_id',
                'as': 'product'
            }},
            {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
            {'$group': {
                '_id': {'$ifNull': ['$product.category', 'Other']},
                'revenue': {'$sum': '$total'}
            }},
            {'$sort': {'revenue': -1}}
        ]
        category_sales_result = list(products_sold.aggregate(category_sales_pipeline, allowDiskUse=True))
        
        category_sales_list = [
            {'category': c['_id'], 'revenue': float(c['revenue'])}
            for c in category_sales_result
        ]
        
        top_category = category_sales_list[0]['category'] if category_sales_list else None
        top_category_revenue = category_sales_list[0]['revenue'] if category_sales_list else 0
        
        # Top customers (with filters) - Optimized with lookup
        top_customers_pipeline = [
            {'$match': base_match},
            {'$group': {
                '_id': '$user_id',
                'total_spent': {'$sum': '$total'},
                'orders': {'$sum': 1}
            }},
            {'$sort': {'total_spent': -1}},
            {'$limit': 100},
            {'$addFields': {
                'user_object_id': {'$toObjectId': '$_id'}
            }},
            {'$lookup': {
                'from': 'users',
                'localField': 'user_object_id',
                'foreignField': '_id',
                'as': 'user'
            }},
            {'$unwind': {'path': '$user', 'preserveNullAndEmptyArrays': True}},
            {'$project': {
                'name': {'$ifNull': ['$user.name', 'Unknown']},
                'email': {'$ifNull': ['$user.email', '']},
                'orders': 1,
                'total_spent': 1
            }}
        ]
        top_customers_result = list(products_sold.aggregate(top_customers_pipeline, allowDiskUse=True))
        
        top_customers = [
            {
                'name': c.get('name', 'Unknown'),
                'email': c.get('email', ''),
                'orders': int(c.get('orders', 0)),
                'total_spent': float(c.get('total_spent', 0))
            }
            for c in top_customers_result
        ]
        
        # Sales trend (daily breakdown with filters) - Optimized single aggregation
        sales_trend_pipeline = [
            {'$match': base_match},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$date'}
                },
                'total': {'$sum': '$total'}
            }},
            {'$sort': {'_id': 1}}
        ]
        sales_trend_result = list(products_sold.aggregate(sales_trend_pipeline, allowDiskUse=True))
        
        # Create a map for quick lookup
        sales_map = {r['_id']: float(r['total']) for r in sales_trend_result}
        
        # Fill in all dates including zeros
        sales_trend = []
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            sales_trend.append({
                'date': current_date.strftime('%m/%d'),
                'sales': sales_map.get(date_key, 0.0)
            })
            current_date += datetime.timedelta(days=1)
        
        return jsonify({
            'total_revenue': total_revenue,  # Changed from 'period_sales'
            'total_orders': total_orders,
            'total_units_sold': total_units,
            'avg_order_value': avg_order_value,
            'active_customers': active_customers,
            'new_customers': new_customers,
            'top_category': top_category,
            'top_category_revenue': top_category_revenue,
            'top_products': top_products,
            'all_products': all_products,
            'category_sales': category_sales_list,
            'top_customers': top_customers,
            'sales_trend': sales_trend
        })
        
    except Exception as e:
        print(f"Error in analytics API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/api/export-analytics-pdf')
def export_analytics_pdf():
    """Export analytics report as PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from flask import make_response
        
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Get analytics data
        pipeline = [
            {
                '$match': {
                    'date': {'$gte': start_date, '$lte': end_date},
                    'total': {'$ne': None}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_sales': {'$sum': '$total'},
                    'total_orders': {'$sum': 1},
                    'unique_customers': {'$addToSet': '$user_id'}
                }
            }
        ]
        
        result = list(db.products_sold.aggregate(pipeline))
        
        if result:
            period_sales = float(result[0].get('total_sales', 0))
            total_orders = result[0].get('total_orders', 0)
            active_customers = len(result[0].get('unique_customers', []))
            avg_order_value = period_sales / total_orders if total_orders > 0 else 0
        else:
            period_sales = 0
            total_orders = 0
            active_customers = 0
            avg_order_value = 0
        
        # Get product performance
        product_pipeline = [
            {
                '$match': {
                    'date': {'$gte': start_date, '$lte': end_date},
                    'total': {'$ne': None}
                }
            },
            {
                '$group': {
                    '_id': '$product_id',
                    'product_name': {'$first': '$product_name'},
                    'total_revenue': {'$sum': '$total'},
                    'total_units': {'$sum': '$quantity'}
                }
            },
            {'$sort': {'total_revenue': -1}},
            {'$limit': 20}
        ]
        
        top_products = list(db.products_sold.aggregate(product_pipeline))
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Sales Analytics Report", title_style)
        elements.append(title)
        
        # Date range
        date_text = f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        date_para = Paragraph(date_text, styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 20))
        
        # Summary metrics
        elements.append(Paragraph("Summary Metrics", heading_style))
        
        # Convert USD to INR
        usd_to_inr = 83.5
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Revenue', f'₹{(period_sales * usd_to_inr):,.2f}'],
            ['Total Orders', f'{total_orders:,}'],
            ['Active Customers', f'{active_customers:,}'],
            ['Average Order Value', f'₹{(avg_order_value * usd_to_inr):,.2f}']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        # Top Products
        if top_products:
            elements.append(Paragraph("Top 20 Products by Revenue", heading_style))
            
            product_data = [['#', 'Product Name', 'Revenue (₹)', 'Units Sold']]
            for idx, product in enumerate(top_products, 1):
                product_data.append([
                    str(idx),
                    product.get('product_name', 'Unknown')[:40],
                    f"₹{(float(product.get('total_revenue', 0)) * usd_to_inr):,.2f}",
                    f"{product.get('total_units', 0):,}"
                ])
            
            product_table = Table(product_data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 1*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(product_table)
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_text = f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-business-summary-pdf')
def export_business_summary_pdf():
    """Export business summary report as PDF"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from flask import make_response
        
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        
        # Get business metrics
        total_sales_pipeline = [
            {'$match': {'total': {'$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        total_sales_result = list(db.products_sold.aggregate(total_sales_pipeline))
        total_sales = float(total_sales_result[0]['total']) if total_sales_result and total_sales_result[0].get('total') else 0.0
        
        total_orders = db.products_sold.count_documents({'total': {'$ne': None}})
        total_users = db.users.count_documents({})
        total_products = db.products_update.count_documents({})
        
        active_users = db.users.count_documents({
            'last_purchase': {'$exists': True, '$ne': None, '$gte': thirty_days_ago}
        })
        
        avg_order = total_sales / total_orders if total_orders > 0 else 0
        
        # Top products
        top_products_pipeline = [
            {'$match': {'date': {'$gte': thirty_days_ago}, 'total': {'$ne': None}}},
            {'$group': {
                '_id': '$product_name',
                'total_revenue': {'$sum': '$total'},
                'units_sold': {'$sum': '$quantity'}
            }},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 10}
        ]
        top_products = list(db.products_sold.aggregate(top_products_pipeline))
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Business Summary Report", title_style)
        elements.append(title)
        
        date_text = f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        date_para = Paragraph(date_text, styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 20))
        
        # Overall metrics
        elements.append(Paragraph("Overall Business Metrics", heading_style))
        
        usd_to_inr = 83.5
        
        overall_data = [
            ['Metric', 'Value'],
            ['Total Revenue (All Time)', f'₹{(total_sales * usd_to_inr):,.2f}'],
            ['Total Orders', f'{total_orders:,}'],
            ['Total Customers', f'{total_users:,}'],
            ['Total Products', f'{total_products:,}'],
            ['Active Customers (30 days)', f'{active_users:,}'],
            ['Average Order Value', f'₹{(avg_order * usd_to_inr):,.2f}']
        ]
        
        overall_table = Table(overall_data, colWidths=[3*inch, 3*inch])
        overall_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(overall_table)
        elements.append(Spacer(1, 30))
        
        # Top products (last 30 days)
        if top_products:
            elements.append(Paragraph("Top 10 Products (Last 30 Days)", heading_style))
            
            product_data = [['#', 'Product Name', 'Revenue (₹)', 'Units']]
            for idx, product in enumerate(top_products, 1):
                product_data.append([
                    str(idx),
                    product.get('_id', 'Unknown')[:35],
                    f"₹{(float(product.get('total_revenue', 0)) * usd_to_inr):,.2f}",
                    f"{product.get('units_sold', 0):,}"
                ])
            
            product_table = Table(product_data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 1*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(product_table)
        
        # Build PDF
        doc.build(elements)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=business_summary_{datetime.datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating business summary PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-report')
def user_report_api():
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Get all users with their purchase data
        user_report_pipeline = [
            {
                '$match': {
                    'date': {'$gte': start_date, '$lte': end_date},
                    'total': {'$ne': None}
                }
            },
            {
                '$group': {
                    '_id': '$user_id',
                    'total_spent': {'$sum': '$total'},
                    'orders': {'$sum': 1},
                    'last_purchase_date': {'$max': '$date'}
                }
            },
            {
                '$sort': {'total_spent': -1}
            }
        ]
        
        user_purchases = list(products_sold.aggregate(user_report_pipeline))
        
        user_report = []
        for up in user_purchases:
            try:
                user = users.find_one({'_id': ObjectId(up['_id'])})
                if user:
                    avg_order = up['total_spent'] / up['orders'] if up['orders'] > 0 else 0
                    last_purchase = up['last_purchase_date'].strftime('%Y-%m-%d %H:%M') if up.get('last_purchase_date') else None
                    
                    user_report.append({
                        'name': user.get('name', 'Unknown'),
                        'email': user.get('email', ''),
                        'orders': int(up['orders']),
                        'total_spent': float(up['total_spent']),
                        'avg_order': float(avg_order),
                        'last_purchase': last_purchase
                    })
            except Exception as e:
                print(f"Error processing user {up['_id']}: {e}")
                continue
        
        return jsonify({
            'users': user_report,
            'total_users': len(user_report)
        })
        
    except Exception as e:
        print(f"Error in user report API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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

@app.route('/admin/festival-notifications')
@admin_required
def admin_festival_notifications():
    """Admin page to view and manage festival notifications"""
    try:
        from festival_notifications import INDIAN_FESTIVALS_2026, get_upcoming_festivals
        
        # Get all festivals
        all_festivals = []
        for festival_name, festival_data in INDIAN_FESTIVALS_2026.items():
            festival_info = festival_data.copy()
            festival_info['days_until'] = (festival_data['date'] - datetime.datetime.now()).days
            all_festivals.append(festival_info)
        
        # Sort by date
        all_festivals.sort(key=lambda x: x['date'])
        
        # Get upcoming festivals (within 30 days)
        upcoming = [f for f in all_festivals if 0 <= f['days_until'] <= 30]
        
        return render_template('festival_notifications.html', 
                             all_festivals=all_festivals,
                             upcoming_festivals=upcoming)
    except Exception as e:
        flash(f'Error loading festival notifications: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-festival-notifications', methods=['POST'])
@admin_required
def admin_send_festival_notifications():
    """Manually trigger festival notifications"""
    try:
        from festival_notifications import send_festival_notifications
        
        # Run the notification system
        send_festival_notifications()
        
        flash('Festival notification check completed successfully!', 'success')
        return jsonify({'success': True, 'message': 'Festival notifications sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/guest-purchase', methods=['POST'])
def guest_purchase():
    """Handle guest checkout purchases"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'variant_name', 'price', 'quantity', 
                          'buyer_name', 'buyer_email', 'buyer_phone', 'delivery_address']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        product_id = ObjectId(data['product_id'])
        variant_name = data['variant_name']
        price = float(data['price'])
        quantity = int(data['quantity'])
        buyer_name = data['buyer_name']
        buyer_email = data['buyer_email']
        buyer_phone = data['buyer_phone']
        delivery_address = data['delivery_address']
        payment_method = data.get('payment_method', 'COD')
        product_name = data.get('product_name', 'Product')
        
        # Validate quantity
        if quantity < 1 or quantity > 10:
            return jsonify({'success': False, 'error': 'Invalid quantity. Must be between 1 and 10'}), 400
        
        # Get product from database
        product = products_update.find_one({'_id': product_id})
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Parse variants if they're strings
        import ast
        if 'variants' in product and isinstance(product['variants'], str):
            try:
                product['variants'] = ast.literal_eval(product['variants'])
            except:
                product['variants'] = []
        
        # Find the specific variant and check stock
        variant_found = False
        variant_stock = 0
        
        if product.get('variants'):
            for variant in product['variants']:
                if variant.get('name', 'Regular') == variant_name:
                    variant_found = True
                    variant_stock = variant.get('stock', 0)
                    break
        else:
            variant_found = True
            variant_stock = product.get('stock', 0)
        
        if not variant_found:
            return jsonify({'success': False, 'error': 'Variant not found'}), 404
        
        if variant_stock < quantity:
            return jsonify({'success': False, 'error': f'Insufficient stock. Only {variant_stock} units available'}), 400
        
        # Calculate total amount
        total_amount = price * quantity
        
        # Create or find user by email
        user = users.find_one({'email': buyer_email})
        
        if not user:
            # Create new user
            user_data = {
                'name': buyer_name,
                'email': buyer_email,
                'phone': buyer_phone,
                'address': delivery_address,
                'join_date': datetime.datetime.now(),
                'created_at': datetime.datetime.now(),
                'is_active': True,
                'loyalty_points': int(total_amount * 0.01),  # 1% of purchase as loyalty points
                'total_purchases': 1,
                'last_purchase': datetime.datetime.now(),
                'email_notifications': True
            }
            user_id = users.insert_one(user_data).inserted_id
        else:
            user_id = user['_id']
            # Update user's purchase info
            users.update_one(
                {'_id': user_id},
                {
                    '$inc': {'total_purchases': 1, 'loyalty_points': int(total_amount * 0.01)},
                    '$set': {'last_purchase': datetime.datetime.now()}
                }
            )
        
        # Create order record
        order_data = {
            'user_id': user_id,
            'product_id': product_id,
            'product_name': product_name,
            'variant': variant_name,
            'quantity': quantity,
            'price': price,
            'total': total_amount,
            'payment_method': payment_method,
            'delivery_address': delivery_address,
            'buyer_name': buyer_name,
            'buyer_email': buyer_email,
            'buyer_phone': buyer_phone,
            'date': datetime.datetime.now(),
            'status': 'confirmed',
            'order_id': f'ORD{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        
        order_result = products_sold.insert_one(order_data)
        order_id = order_data['order_id']
        
        # Update product stock
        if product.get('variants'):
            # Update specific variant stock
            updated_variants = []
            for variant in product['variants']:
                if variant.get('name', 'Regular') == variant_name:
                    variant['stock'] = variant.get('stock', 0) - quantity
                updated_variants.append(variant)
            
            products_update.update_one(
                {'_id': product_id},
                {'$set': {'variants': updated_variants}}
            )
        else:
            # Update direct stock
            products_update.update_one(
                {'_id': product_id},
                {'$inc': {'stock': -quantity}}
            )
        
        # Send confirmation email (optional - if SMTP is configured)
        try:
            send_order_confirmation_email(buyer_email, buyer_name, order_data)
        except Exception as email_error:
            print(f"Could not send confirmation email: {email_error}")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'total_amount': f"{total_amount:.2f}",
            'message': 'Purchase successful!'
        })
        
    except Exception as e:
        print(f"Error processing purchase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def send_order_confirmation_email(email, name, order_data):
    """Send order confirmation email to buyer"""
    try:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
        SMTP_EMAIL = os.getenv('SMTP_EMAIL')
        SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("SMTP credentials not configured")
            return
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Order Confirmation - {order_data['order_id']}"
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                    <h1>Order Confirmed! 🎉</h1>
                </div>
                
                <div style="padding: 20px; background: #f9f9f9;">
                    <h2>Dear {name},</h2>
                    <p>Thank you for your purchase! Your order has been confirmed.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>Order Details</h3>
                        <p><strong>Order ID:</strong> {order_data['order_id']}</p>
                        <p><strong>Product:</strong> {order_data['product_name']}</p>
                        <p><strong>Variant:</strong> {order_data['variant']}</p>
                        <p><strong>Quantity:</strong> {order_data['quantity']}</p>
                        <p><strong>Price per unit:</strong> ₹{order_data['price']:.2f}</p>
                        <p><strong>Total Amount:</strong> <span style="color: #28a745; font-size: 1.2em;">₹{order_data['total']:.2f}</span></p>
                        <p><strong>Payment Method:</strong> {order_data['payment_method']}</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>Delivery Address</h3>
                        <p>{order_data['delivery_address']}</p>
                    </div>
                    
                    <p>Your order will be processed and shipped within 2-3 business days.</p>
                    <p>For any queries, please contact us at support@salessense.com</p>
                    
                    <p style="margin-top: 30px;">
                        Best regards,<br>
                        <strong>Sales Sense AI Team</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"✅ Confirmation email sent to {email}")
    except Exception as e:
        print(f"❌ Error sending confirmation email: {e}")
        raise

# ============================================
# PROJECT ASSISTANT CHATBOT API
# ============================================

@app.route('/api/project-assistant', methods=['POST'])
def project_assistant():
    """
    LLM-based chatbot for answering questions about the Sales Sense AI project.
    Uses predefined knowledge base with smart matching.
    """
    try:
        data = request.get_json()
        question = data.get('question', '').lower().strip()
        
        if not question:
            return jsonify({'answer': 'Please ask me a question about Sales Sense AI!'})
        
        # Get current stats for dynamic responses
        try:
            total_users = users.count_documents({}) if users is not None else 1750
            total_products = products_update.count_documents({}) if products_update is not None else 77
            
            # Calculate total revenue
            total_sales_pipeline = [{'$group': {'_id': None, 'total': {'$sum': '$total'}}}]
            total_sales_result = list(products_sold.aggregate(total_sales_pipeline)) if products_sold is not None else []
            total_revenue = float(total_sales_result[0]['total']) if total_sales_result else 14957457.66
            
            # Today's sales
            today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
            sales_today_pipeline = [
                {'$match': {'date': {'$gte': today}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
            ]
            sales_today_result = list(products_sold.aggregate(sales_today_pipeline)) if products_sold is not None else []
            sales_today = float(sales_today_result[0]['total']) if sales_today_result else 88.47
            
            new_users_today = users.count_documents({'created_at': {'$gte': today}}) if users is not None else 0
        except:
            total_users = 1750
            total_products = 77
            total_revenue = 14957457.66
            sales_today = 88.47
            new_users_today = 0
        
        # Knowledge base with predefined Q&A
        knowledge_base = {
            'what is sales sense ai': {
                'keywords': ['what is', 'about', 'sales sense', 'project', 'tell me'],
                'answer': """🎯 <strong>Sales Sense AI</strong> is an intelligent business management platform that helps you:<br><br>
                📊 <strong>Track Sales & Analytics</strong> - Real-time revenue tracking and business insights<br>
                👥 <strong>Manage Users</strong> - Complete user management with activity tracking<br>
                📦 <strong>Inventory Control</strong> - Stock monitoring with low-stock alerts<br>
                🎉 <strong>Festival Marketing</strong> - Automated email campaigns for Indian festivals<br>
                👷 <strong>Worker Management</strong> - Track worker activities and productivity<br>
                💰 <strong>Guest Checkout</strong> - Allow purchases without user registration<br><br>
                Built with Flask, MongoDB, and powered by AI insights! 🚀"""
            },
            'users': {
                'keywords': ['user', 'customer', 'how many users', 'total users', 'user count'],
                'answer': f"""👥 <strong>User Statistics:</strong><br><br>
                📈 Total Users: <strong>{total_users:,}</strong><br>
                ✨ New Today: <strong>{new_users_today}</strong><br>
                🛒 Guest Checkout: <strong>Enabled</strong><br><br>
                Users can register, browse products, make purchases, and receive order confirmations via email!"""
            },
            'features': {
                'keywords': ['feature', 'capability', 'can do', 'functionality', 'what does'],
                'answer': """✨ <strong>Key Features:</strong><br><br>
                <strong>1. Admin Dashboard 🎯</strong><br>
                • Real-time business metrics<br>
                • Sales analytics & charts<br>
                • User & worker management<br><br>
                <strong>2. Smart Inventory 📦</strong><br>
                • Multi-variant products<br>
                • Low stock alerts<br>
                • Stock value tracking in ₹<br><br>
                <strong>3. Festival Marketing 🎉</strong><br>
                • 12 Indian festivals tracked<br>
                • Automated email campaigns<br>
                • Product recommendations<br><br>
                <strong>4. Guest Checkout 🛒</strong><br>
                • No login required<br>
                • Email confirmations<br>
                • Dynamic stock updates<br><br>
                <strong>5. Worker Portal 👷</strong><br>
                • Activity tracking<br>
                • Product management<br>
                • Performance metrics"""
            },
            'festival': {
                'keywords': ['festival', 'notification', 'email', 'marketing', 'diwali', 'holi'],
                'answer': """🎉 <strong>Festival Notification System:</strong><br><br>
                📅 <strong>12 Indian Festivals Tracked:</strong><br>
                Pongal, Holi, Ram Navami, Akshaya Tritiya, Eid, Raksha Bandhan, Janmashtami, Ganesh Chaturthi, Navaratri, Dussehra, Diwali, Christmas<br><br>
                📧 <strong>How it works:</strong><br>
                • Checks daily for upcoming festivals<br>
                • Sends emails 7 days before festival<br>
                • Smart product recommendations<br>
                • Discount offers (10-40%)<br>
                • HTML formatted emails<br><br>
                💡 Helps boost sales during festival seasons!"""
            },
            'analytics': {
                'keywords': ['analytic', 'report', 'sales', 'revenue', 'chart', 'graph'],
                'answer': f"""📊 <strong>Analytics Dashboard:</strong><br><br>
                💰 <strong>Revenue:</strong><br>
                • Total Revenue: ₹{total_revenue:,.2f}<br>
                • Today's Sales: ₹{sales_today:,.2f}<br><br>
                📈 <strong>Visualizations:</strong><br>
                • 7-day sales trends<br>
                • Category-wise breakdown<br>
                • Top performing products<br>
                • Worker productivity charts<br><br>
                📦 <strong>Inventory:</strong><br>
                • Total Products: {total_products}<br>
                • Low Stock Alerts: Monitored<br>
                • Stock Value Tracking"""
            },
            'products': {
                'keywords': ['product', 'inventory', 'stock', 'item', 'catalog'],
                'answer': """📦 <strong>Product Management:</strong><br><br>
                <strong>Features:</strong><br>
                • Multi-variant support (size, color, etc.)<br>
                • Price in Indian Rupees (₹)<br>
                • Stock tracking per variant<br>
                • Category organization<br>
                • Image uploads<br>
                • Low stock alerts (<10 units)<br><br>
                <strong>Stock Display:</strong><br>
                🟢 High Stock: >50 units<br>
                🟡 Medium Stock: 10-50 units<br>
                🔴 Low Stock: <10 units<br><br>
                Stock values capped at 1024 for better display!"""
            },
            'workers': {
                'keywords': ['worker', 'staff', 'employee', 'team'],
                'answer': """👷 <strong>Worker Management:</strong><br><br>
                <strong>Features:</strong><br>
                • Worker registration & login<br>
                • Activity tracking<br>
                • Product addition rights<br>
                • Performance monitoring<br>
                • Last active timestamps<br><br>
                <strong>Capabilities:</strong><br>
                • Add new products<br>
                • Update inventory<br>
                • View sales reports<br>
                • Access worker dashboard<br><br>
                Admins can activate/deactivate workers and reset passwords!"""
            },
            'database': {
                'keywords': ['database', 'mongodb', 'data', 'storage', 'collection'],
                'answer': """🗄️ <strong>Database Architecture:</strong><br><br>
                <strong>MongoDB Collections:</strong><br>
                • <code>users</code> - Customer data (1,750 users)<br>
                • <code>products_update</code> - Product catalog (77 products)<br>
                • <code>products_sold</code> - Sales transactions<br>
                • <code>workers_update</code> - Worker accounts<br>
                • <code>admins</code> - Admin credentials<br>
                • <code>email_history</code> - Email logs<br><br>
                <strong>Cloud Hosted:</strong><br>
                MongoDB Atlas cluster with automatic backups and encryption!"""
            },
            'technology': {
                'keywords': ['tech', 'technology', 'stack', 'built', 'framework', 'language'],
                'answer': """💻 <strong>Technology Stack:</strong><br><br>
                <strong>Backend:</strong><br>
                • Python 3.10<br>
                • Flask Framework<br>
                • PyMongo (MongoDB driver)<br>
                • SMTP for emails<br><br>
                <strong>Frontend:</strong><br>
                • Bootstrap 5<br>
                • Jinja2 Templates<br>
                • Chart.js for visualizations<br>
                • Responsive design<br><br>
                <strong>Database:</strong><br>
                • MongoDB Atlas<br>
                • Cloud-hosted<br><br>
                <strong>Deployment:</strong><br>
                • Ready for Render/Heroku<br>
                • Environment variables<br>
                • Production WSGI support"""
            },
            'help': {
                'keywords': ['help', 'support', 'how to', 'tutorial', 'guide'],
                'answer': """🆘 <strong>Need Help?</strong><br><br>
                <strong>Quick Start:</strong><br>
                1. Use the sidebar to navigate sections<br>
                2. Click "Overview" for dashboard<br>
                3. "Users" to manage customers<br>
                4. "Product Reports" for inventory<br>
                5. "Festival Notifications" for marketing<br><br>
                <strong>Common Tasks:</strong><br>
                • View user details: Click "View" button<br>
                • Reset password: Use reset option<br>
                • Send emails: Use Email Marketing<br>
                • Check stock: Go to Product Reports<br><br>
                💡 Hover over buttons to see tooltips!"""
            }
        }
        
        # Smart matching algorithm
        best_match = None
        best_score = 0
        
        for category, data in knowledge_base.items():
            score = 0
            for keyword in data['keywords']:
                if keyword in question:
                    score += question.count(keyword) * 2
                    # Boost score if keyword appears early in question
                    if question.startswith(keyword):
                        score += 3
            
            if score > best_score:
                best_score = score
                best_match = data['answer']
        
        # Fallback response
        if best_score == 0:
            return jsonify({
                'answer': """🤔 I'm not sure about that. Here's what I can help you with:<br><br>
                • <strong>General Info:</strong> "What is Sales Sense AI?"<br>
                • <strong>Users:</strong> "How many users do we have?"<br>
                • <strong>Features:</strong> "What features are available?"<br>
                • <strong>Festival Marketing:</strong> "How does festival notification work?"<br>
                • <strong>Analytics:</strong> "Tell me about analytics"<br>
                • <strong>Products:</strong> "How does inventory work?"<br>
                • <strong>Workers:</strong> "Tell me about worker management"<br>
                • <strong>Technology:</strong> "What technology is used?"<br><br>
                Try asking one of these questions! 😊"""
            })
        
        return jsonify({'answer': best_match})
        
    except Exception as e:
        print(f"Error in project assistant: {e}")
        return jsonify({
            'answer': '⚠️ Sorry, I encountered an error. Please try again or contact support.'
        }), 500

# ============================================
# EMAIL TEST API
# ============================================

@app.route('/api/test-email', methods=['POST'])
@admin_required
def test_email():
    """
    Send a test email to verify email configuration
    """
    try:
        data = request.get_json()
        recipient_email = data.get('email', '').strip()
        
        if not recipient_email or '@' not in recipient_email:
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Get email configuration
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            return jsonify({
                'success': False, 
                'error': 'Email not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file'
            }), 500
        
        # Create test email
        message = MIMEMultipart('alternative')
        message['Subject'] = '🎉 Sales Sense AI - Test Email'
        message['From'] = sender_email
        message['To'] = recipient_email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; color: #155724; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Test Email Successful!</h1>
                </div>
                <div class="content">
                    <div class="success">
                        <h2>🎉 Congratulations!</h2>
                        <p>Your email system is working perfectly!</p>
                    </div>
                    
                    <h3>✨ What This Means:</h3>
                    <ul>
                        <li>✅ SMTP connection is configured correctly</li>
                        <li>✅ Authentication is successful</li>
                        <li>✅ Emails can be sent from your application</li>
                        <li>✅ Order confirmations will work</li>
                        <li>✅ Festival notifications will be delivered</li>
                    </ul>
                    
                    <h3>📧 Email Features Ready:</h3>
                    <ul>
                        <li>🛒 Order confirmation emails</li>
                        <li>🎉 Festival notification emails</li>
                        <li>📊 Purchase receipts</li>
                        <li>🎁 Marketing campaigns</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">
                        <strong>From:</strong> Sales Sense AI<br>
                        <strong>Platform:</strong> Business Intelligence & Sales Management<br>
                        <strong>Status:</strong> All Systems Operational 🚀
                    </p>
                </div>
                <div class="footer">
                    <p>This is a test email from Sales Sense AI</p>
                    <p>&copy; 2026 Sales Sense AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        
        return jsonify({
            'success': True, 
            'message': f'Test email sent successfully to {recipient_email}'
        })
        
    except smtplib.SMTPAuthenticationError:
        return jsonify({
            'success': False, 
            'error': 'Email authentication failed. Check SENDER_EMAIL and SENDER_PASSWORD'
        }), 500
    except Exception as e:
        print(f"Error sending test email: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Start auto-refresh background thread
    start_auto_refresh_thread()
    
    # Start festival notification checker (runs daily)
    try:
        from festival_notifications import run_notification_scheduler
        notification_thread = threading.Thread(target=run_notification_scheduler, args=(24,), daemon=True)
        notification_thread.start()
        print("✅ Festival notification scheduler started!")
    except Exception as e:
        print(f"⚠️  Festival notification scheduler not started: {e}")
    
    # Use environment variable for port (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)