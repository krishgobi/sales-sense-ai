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
@app.template_filter('truncate')
def truncate_filter(text, length=20):
    """Truncate text to specified length"""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length] + '...'

@app.template_filter('strftime')
def strftime_filter(date, format='%Y-%m-%d'):
    """Format a date string"""
    try:
        if isinstance(date, str):
            return datetime.datetime.now().strftime(format)
        return date.strftime(format)
    except:
        return datetime.datetime.now().strftime(format)

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
    try:
        # Get basic statistics for home page
        total_users = users.count_documents({})
        new_users_today = users.count_documents({
            'join_date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        }) if users.find_one() else 0
        
        total_products = products_update.count_documents({})
        total_categories = len(set(product.get('category', 'Uncategorized') 
                                for product in products_update.find()))
        
        total_workers = workers_update.count_documents({})
        active_workers = workers_update.count_documents({
            'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
        })
        
        # Calculate total sales
        total_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())
        sales_today = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
            'date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        }))
        
        home_stats = {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_sales': total_sales,
            'sales_today': sales_today,
            'total_products': total_products,
            'total_categories': total_categories,
            'total_workers': total_workers,
            'active_workers': active_workers
        }
        
        # Get recent users (last 5)
        recent_users = list(users.find().sort('join_date', -1).limit(5))
        
        # Get recent sales (last 5)
        recent_sales = []
        sales_cursor = products_sold.find().sort('date', -1).limit(5)
        for sale in sales_cursor:
            # Get user name for the sale
            user = users.find_one({'_id': sale.get('user_id')})
            sale['user_name'] = user.get('name', 'Anonymous') if user else 'Anonymous'
            recent_sales.append(sale)
        
        # Get top products (top 6)
        product_sales = {}
        for sale in products_sold.find():
            product_id = sale['product_id']
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'name': sale.get('product_name', 'Unknown Product'),
                    'units_sold': 0,
                    'revenue': 0.0
                }
            
            try:
                quantity = int(float(str(sale.get('quantity', '0')).replace(',', '')))
                product_sales[product_id]['units_sold'] += quantity
                sale_amount = float(calculate_sale_amount(sale))
                product_sales[product_id]['revenue'] += sale_amount
            except (ValueError, TypeError):
                continue
        
        top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:6]
        
        return render_template('home.html', 
                             home_stats=home_stats,
                             recent_users=recent_users,
                             recent_sales=recent_sales,
                             top_products=top_products)
    
    except Exception as e:
        print(f"Error loading home page: {e}")
        # Return basic home page with empty data
        return render_template('home.html',
                             home_stats={'total_users': 0, 'new_users_today': 0, 'total_sales': 0.0, 'sales_today': 0.0, 'total_products': 0, 'total_categories': 0, 'total_workers': 0, 'active_workers': 0},
                             recent_users=[],
                             recent_sales=[],
                             top_products=[])

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
            return redirect(url_for('admin_dashboard'))
    
    # Update last activity and proceed to admin panel
    session['last_activity'] = datetime.datetime.utcnow().timestamp()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Get statistics
        stats = {
            'total_users': users.count_documents({}),
            'new_users_today': users.count_documents({
                'created_at': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
            }),
            'total_sales': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())),
            'sales_today': float(sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
                'date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
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

        # Get user data
        users_data = list(users.find().sort('join_date', -1).limit(10))
        for user in users_data:
            # Convert ObjectId to string for JSON serialization
            user['_id'] = str(user['_id'])
            user_orders = list(products_sold.find({'user_id': ObjectId(user['_id'])}))
            # Convert ObjectIds in orders as well
            for order in user_orders:
                order['_id'] = str(order['_id'])
                order['user_id'] = str(order['user_id'])
                order['product_id'] = str(order['product_id'])
            user['orders'] = user_orders
            user['total_spent'] = float(sum(float(calculate_sale_amount(order)) for order in user_orders))

        # Get product data
        products_data = list(products_update.find())
        for product in products_data:
            product['_id'] = str(product['_id'])
            if 'added_by' in product:
                product['added_by'] = str(product['added_by'])

        # Get worker data
        workers_data = list(workers_update.find())
        for worker in workers_data:
            worker['_id'] = str(worker['_id'])
            worker_products = list(worker_specific_added.find({'worker_id': ObjectId(worker['_id'])}))
            # Convert ObjectIds in worker products
            for wp in worker_products:
                wp['_id'] = str(wp['_id'])
                wp['worker_id'] = str(wp['worker_id'])
                wp['product_id'] = str(wp['product_id'])
            worker['products_added'] = worker_products

        # Generate real sales data for charts from actual sales
        sales_by_date = {}
        try:
            for sale in products_sold.find():
                sale_date = sale.get('date', datetime.datetime.utcnow())
                if isinstance(sale_date, datetime.datetime):
                    date_str = sale_date.strftime('%Y-%m-%d')
                else:
                    date_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
                
                if date_str not in sales_by_date:
                    sales_by_date[date_str] = 0.0
                
                sale_amount = float(calculate_sale_amount(sale))
                sales_by_date[date_str] += sale_amount
        except Exception as e:
            print(f"Error processing sales data: {e}")

        # Get last 7 days of sales data
        today = datetime.datetime.now()
        sales_dates = []
        sales_values = []
        
        for i in range(6, -1, -1):  # Last 7 days
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            sales_dates.append(date_str)
            sales_values.append(sales_by_date.get(date_str, 0.0))

        sales_data = {
            'dates': sales_dates,
            'values': sales_values
        }

        # Generate category data from actual products
        category_sales = {}
        category_counts = {}
        try:
            for product in products_update.find():
                category = product.get('category', 'Uncategorized')
                if category not in category_counts:
                    category_counts[category] = 0
                    category_sales[category] = 0.0
                category_counts[category] += 1
                
                # Calculate sales for this product
                for sale in products_sold.find({'product_id': product['_id']}):
                    sale_amount = float(calculate_sale_amount(sale))
                    category_sales[category] += sale_amount
        except Exception as e:
            print(f"Error processing category data: {e}")

        category_data = {
            'labels': list(category_sales.keys())[:5],  # Top 5 categories
            'values': [category_sales[cat] for cat in list(category_sales.keys())[:5]]
        }

        # Generate product summary reports
        product_categories = []
        low_stock_items = []
        total_stock_value = 0.0
        
        category_summary = {}
        try:
            for product in products_update.find():
                category = product.get('category', 'Uncategorized')
                if category not in category_summary:
                    category_summary[category] = {'product_count': 0, 'total_stock': 0}
                
                category_summary[category]['product_count'] += 1
                
                # Process variants for stock and value calculations
                for variant in product.get('variants', []):
                    if isinstance(variant, dict):
                        stock = int(variant.get('stock', 0)) if variant.get('stock') is not None else 0
                        price = safe_float(variant.get('price', 0))
                        
                        category_summary[category]['total_stock'] += stock
                        total_stock_value += float(stock) * float(price)
                        
                        # Check for low stock items
                        if stock < 10 and stock > 0:
                            low_stock_items.append({
                                'product_name': product.get('name', 'Unknown'),
                                'variant_name': variant.get('quantity', 'Default'),
                                'stock': stock
                            })
        except Exception as e:
            print(f"Error processing product summary: {e}")
            total_stock_value = 0.0

        # Convert to list format for template
        for category, data in category_summary.items():
            product_categories.append({
                'name': category,
                'product_count': data['product_count'],
                'total_stock': data['total_stock']
            })

        # Sort categories by stock count
        product_categories.sort(key=lambda x: x['total_stock'], reverse=True)
        
        # Ensure total_stock_value is always a valid float
        product_summary = {
            'total_stock_value': float(total_stock_value) if total_stock_value is not None else 0.0
        }

        # Get top selling products with category information
        top_products = []
        product_sales = {}
        try:
            for sale in products_sold.find():
                product_id = sale['product_id']
                if product_id not in product_sales:
                    # Get product details for category
                    product_details = products_update.find_one({'_id': product_id})
                    product_sales[product_id] = {
                        'name': sale.get('product_name', 'Unknown Product'),
                        'category': product_details.get('category', 'Uncategorized') if product_details else 'Uncategorized',
                        'units_sold': 0,
                        'revenue': 0.0
                    }
                try:
                    # Convert quantity to integer, defaulting to 0 if invalid
                    quantity = int(float(str(sale.get('quantity', '0')).replace(',', '')))
                    product_sales[product_id]['units_sold'] += quantity
                    
                    # Calculate sale amount using our helper function
                    sale_amount = float(calculate_sale_amount(sale))  # Ensure float conversion
                    product_sales[product_id]['revenue'] += sale_amount
                except (ValueError, TypeError) as e:
                    print(f"Error processing sale {sale.get('_id')}: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error processing top products: {e}")

        top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:5]

        # Ensure all numeric values in stats are proper types with safe defaults
        stats = {
            'total_users': int(stats.get('total_users', 0)),
            'new_users_today': int(stats.get('new_users_today', 0)),
            'total_sales': float(stats.get('total_sales', 0.0)),
            'sales_today': float(stats.get('sales_today', 0.0)),
            'total_products': int(stats.get('total_products', 0)),
            'low_stock_products': int(stats.get('low_stock_products', 0)),
            'total_workers': int(stats.get('total_workers', 0)),
            'active_workers': int(stats.get('active_workers', 0))
        }

        # Convert any numeric values in top_products to appropriate types
        for product in top_products:
            product['units_sold'] = int(product.get('units_sold', 0))
            product['revenue'] = float(product.get('revenue', 0.0))

        return render_template('admin_dashboard.html',
                             stats=stats,
                             users=users_data,
                             workers=workers_data,
                             sales_data=sales_data,
                             category_data=category_data,
                             top_products=top_products,
                             product_categories=product_categories,
                             low_stock_items=low_stock_items,
                             product_summary=product_summary)
    
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        # Return a safe fallback response
        return render_template('admin_dashboard.html',
                             stats={'total_users': 0, 'new_users_today': 0, 'total_sales': 0.0, 'sales_today': 0.0, 'total_products': 0, 'low_stock_products': 0, 'total_workers': 0, 'active_workers': 0},
                             users=[],
                             workers=[],
                             sales_data={'dates': [], 'values': []},
                             category_data={'labels': [], 'values': []},
                             top_products=[],
                             product_categories=[],
                             low_stock_items=[],
                             product_summary={'total_stock_value': 0.0})

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
            sale_amount = float(calculate_sale_amount(sale))  # Ensure float conversion
            product_sales[sale['product_id']]['revenue'] += sale_amount
        except (ValueError, TypeError) as e:
            print(f"Error processing sale {sale.get('_id')}: {str(e)}")
            continue

    top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:5]

    # Ensure all numeric values in stats are floats
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

    # Convert any numeric values in top_products to appropriate types
    for product in top_products:
        product['units_sold'] = int(product['units_sold'])
        product['revenue'] = float(product['revenue'])

    return render_template('admin_dashboard.html',
                         stats=stats,
                         users=users_data,
                         products=products_data,
                         workers=workers_data,
                         sales_data=sales_data,
                         category_data=category_data,
                         top_products=top_products)

@app.route('/admin/chatbot', methods=['POST'])
@admin_required
def admin_chatbot():
    """AI Chatbot for admin queries with function matching"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower().strip()
        chat_history = data.get('history', [])
        
        # Define chatbot functions with patterns and responses
        chatbot_functions = {
            'sales_report': {
                'patterns': ['sales', 'revenue', 'money', 'earnings', 'income', 'profit'],
                'function': get_sales_report
            },
            'user_stats': {
                'patterns': ['users', 'customers', 'members', 'people', 'accounts'],
                'function': get_user_stats
            },
            'product_info': {
                'patterns': ['products', 'items', 'inventory', 'stock', 'catalog'],
                'function': get_product_info
            },
            'worker_info': {
                'patterns': ['workers', 'employees', 'staff', 'team'],
                'function': get_worker_info
            },
            'top_products': {
                'patterns': ['top products', 'best selling', 'popular', 'trending'],
                'function': get_top_products_info
            },
            'system_status': {
                'patterns': ['status', 'health', 'system', 'overview', 'summary'],
                'function': get_system_status
            },
            'help': {
                'patterns': ['help', 'what can you do', 'commands', 'options'],
                'function': get_help_info
            }
        }
        
        # Find the best matching function
        best_match = None
        best_score = 0
        
        for func_name, func_data in chatbot_functions.items():
            score = 0
            for pattern in func_data['patterns']:
                if pattern in user_message:
                    score += len(pattern.split())  # Longer phrases get higher scores
            
            if score > best_score:
                best_score = score
                best_match = func_data['function']
        
        # Generate response
        if best_match and best_score > 0:
            response = best_match()
        else:
            response = get_default_response(user_message)
        
        # Store chat in database for history
        chat_entry = {
            'user_message': data.get('message', ''),
            'bot_response': response,
            'timestamp': datetime.datetime.utcnow(),
            'admin_id': session.get('admin_id')
        }
        
        # Store in a chat_history collection
        try:
            db.chat_history.insert_one(chat_entry)
        except Exception as e:
            print(f"Error storing chat history: {e}")
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"Error in chatbot: {e}")
        return jsonify({
            'success': False,
            'error': 'Sorry, I encountered an error processing your request.'
        })

def get_sales_report():
    """Generate sales report"""
    try:
        total_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())
        sales_today = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find({
            'date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        }))
        
        total_orders = products_sold.count_documents({})
        orders_today = products_sold.count_documents({
            'date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        })
        
        return f"""📊 **Sales Report:**
        
💰 **Total Revenue:** ${total_sales:.2f}
📈 **Today's Sales:** ${sales_today:.2f}
📦 **Total Orders:** {total_orders}
🛒 **Today's Orders:** {orders_today}
📊 **Average Order Value:** ${(total_sales/total_orders):.2f if total_orders > 0 else 0}

{get_growth_insight(sales_today, total_sales)}"""
        
    except Exception as e:
        return "Sorry, I couldn't retrieve the sales data at the moment."

def get_user_stats():
    """Generate user statistics"""
    try:
        total_users = users.count_documents({})
        new_users_today = users.count_documents({
            'join_date': {'$gte': datetime.datetime.now().replace(hour=0, minute=0, second=0)}
        })
        
        # Get recent user activity
        recent_orders = products_sold.count_documents({
            'date': {'$gte': datetime.datetime.now() - datetime.timedelta(days=7)}
        })
        
        return f"""👥 **User Statistics:**
        
👤 **Total Users:** {total_users}
🆕 **New Users Today:** {new_users_today}
🛍️ **Orders This Week:** {recent_orders}
📊 **Active Rate:** {(recent_orders/total_users*100):.1f}% if total_users > 0 else 0%

💡 **Insight:** {"Great growth!" if new_users_today > 0 else "Focus on user acquisition strategies."}"""
        
    except Exception as e:
        return "Sorry, I couldn't retrieve the user statistics at the moment."

def get_product_info():
    """Generate product information"""
    try:
        total_products = products_update.count_documents({})
        
        # Count low stock items
        low_stock_count = 0
        total_stock_value = 0.0
        
        for product in products_update.find():
            for variant in product.get('variants', []):
                if isinstance(variant, dict):
                    stock = variant.get('stock', 0)
                    price = safe_float(variant.get('price', 0))
                    total_stock_value += stock * price
                    
                    if stock < 10:
                        low_stock_count += 1
        
        categories = len(set(product.get('category', 'Uncategorized') 
                           for product in products_update.find()))
        
        return f"""📦 **Product Information:**
        
🏷️ **Total Products:** {total_products}
📂 **Categories:** {categories}
⚠️ **Low Stock Items:** {low_stock_count}
💎 **Total Stock Value:** ${total_stock_value:.2f}

{"🔔 **Alert:** Some items are running low on stock!" if low_stock_count > 0 else "✅ **Stock Status:** All items are well stocked."}"""
        
    except Exception as e:
        return "Sorry, I couldn't retrieve the product information at the moment."

def get_worker_info():
    """Generate worker information"""
    try:
        total_workers = workers_update.count_documents({})
        active_workers = workers_update.count_documents({
            'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
        })
        
        # Get worker productivity
        total_products_added = sum(worker.get('total_products_added', 0) 
                                 for worker in workers_update.find())
        
        return f"""👷 **Worker Information:**
        
👥 **Total Workers:** {total_workers}
✅ **Active (24h):** {active_workers}
📦 **Products Added:** {total_products_added}
📊 **Activity Rate:** {(active_workers/total_workers*100):.1f}% if total_workers > 0 else 0%

💼 **Average Productivity:** {(total_products_added/total_workers):.1f} products per worker if total_workers > 0 else 0"""
        
    except Exception as e:
        return "Sorry, I couldn't retrieve the worker information at the moment."

def get_top_products_info():
    """Get top selling products"""
    try:
        product_sales = {}
        for sale in products_sold.find():
            product_id = sale['product_id']
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'name': sale.get('product_name', 'Unknown Product'),
                    'revenue': 0.0,
                    'units_sold': 0
                }
            
            try:
                quantity = int(float(str(sale.get('quantity', '0')).replace(',', '')))
                product_sales[product_id]['units_sold'] += quantity
                sale_amount = float(calculate_sale_amount(sale))
                product_sales[product_id]['revenue'] += sale_amount
            except (ValueError, TypeError):
                continue
        
        top_products = sorted(product_sales.values(), key=lambda x: x['revenue'], reverse=True)[:5]
        
        if not top_products:
            return "📈 **Top Products:** No sales data available yet."
        
        response = "🏆 **Top Selling Products:**\n\n"
        for i, product in enumerate(top_products, 1):
            response += f"{i}. **{product['name']}**\n"
            response += f"   💰 Revenue: ${product['revenue']:.2f}\n"
            response += f"   📦 Units Sold: {product['units_sold']}\n\n"
        
        return response
        
    except Exception as e:
        return "Sorry, I couldn't retrieve the top products information at the moment."

def get_system_status():
    """Generate system overview"""
    try:
        # Get all key metrics
        users_count = users.count_documents({})
        products_count = products_update.count_documents({})
        workers_count = workers_update.count_documents({})
        total_sales = sum(float(calculate_sale_amount(sale)) for sale in products_sold.find())
        
        return f"""🖥️ **System Status Overview:**
        
🟢 **System Status:** Online and Operational
👥 **Users:** {users_count}
📦 **Products:** {products_count}
👷 **Workers:** {workers_count}
💰 **Total Revenue:** ${total_sales:.2f}

🔧 **Database:** Connected
📊 **All systems functioning normally**"""
        
    except Exception as e:
        return "🔴 **System Status:** Some issues detected. Please check the system logs."

def get_help_info():
    """Show available commands"""
    return """🤖 **SalesSense AI Assistant Help:**

I can help you with the following:

📊 **Sales & Revenue:**
- "Show me sales report"
- "What's today's revenue?"
- "How many orders today?"

👥 **Users & Customers:**
- "How many users do we have?"
- "Show user statistics"
- "New users today?"

📦 **Products & Inventory:**
- "Product information"
- "Stock status"
- "Low stock items"

🏆 **Performance:**
- "Top selling products"
- "Best performers"
- "Popular items"

👷 **Workers & Team:**
- "Worker information"
- "Active workers"
- "Team productivity"

🖥️ **System:**
- "System status"
- "Overview"
- "Health check"

Just ask me anything about your SalesSense system!"""

def get_growth_insight(sales_today, total_sales):
    """Generate growth insights"""
    if total_sales > 0:
        daily_avg = total_sales / 30  # Rough estimate
        if sales_today > daily_avg:
            return "📈 **Insight:** Today's sales are above average! Great performance!"
        elif sales_today > 0:
            return "📊 **Insight:** Steady sales day. Consider promotional activities to boost revenue."
        else:
            return "📉 **Insight:** No sales yet today. Time to implement marketing strategies!"
    return "📊 **Insight:** Starting fresh! Focus on customer acquisition and engagement."

def get_default_response(message):
    """Generate default response for unmatched queries"""
    responses = [
        "I'm not sure I understand that question. Could you try asking about sales, users, products, or workers?",
        "I can help you with sales reports, user statistics, product information, and worker data. What would you like to know?",
        "Sorry, I didn't catch that. Try asking 'help' to see what I can do for you!",
        "I'm here to help with your SalesSense data. Ask me about sales, users, products, or system status!"
    ]
    
    # Simple keyword matching for better responses
    if any(word in message for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm your SalesSense AI Assistant. How can I help you today? Ask me about sales, users, products, or workers!"
    elif any(word in message for word in ['thank', 'thanks']):
        return "You're welcome! Is there anything else you'd like to know about your SalesSense system?"
    elif any(word in message for word in ['bye', 'goodbye']):
        return "Goodbye! Feel free to ask me anything about your SalesSense data anytime!"
    
    import random
    return random.choice(responses)

@app.route('/admin/chat-history')
@admin_required
def admin_chat_history():
    """View chat history"""
    try:
        chat_entries = list(db.chat_history.find(
            {'admin_id': session.get('admin_id')}
        ).sort('timestamp', -1).limit(50))
        
        for entry in chat_entries:
            entry['_id'] = str(entry['_id'])
        
        return jsonify({'success': True, 'history': chat_entries})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/user-details/<user_id>')
@admin_required
def admin_user_details(user_id):
    """View detailed information about a specific user"""
    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Convert ObjectId to string for template
        user['_id'] = str(user['_id'])
        
        # Get user's purchase history
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        for order in user_orders:
            order['_id'] = str(order['_id'])
            order['user_id'] = str(order['user_id'])
            order['product_id'] = str(order['product_id'])
        
        # Calculate user statistics
        total_spent = sum(float(calculate_sale_amount(order)) for order in user_orders)
        total_orders = len(user_orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Calculate days since last order
        last_order_days = 'N/A'
        if user_orders:
            last_order = max(user_orders, key=lambda x: x.get('date', datetime.datetime.min))
            if last_order.get('date'):
                last_order_date = last_order['date']
                if isinstance(last_order_date, datetime.datetime):
                    days_diff = (datetime.datetime.utcnow() - last_order_date).days
                    last_order_days = f"{days_diff} days ago" if days_diff > 0 else "Today"
        
        user_stats = {
            'total_orders': total_orders,
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'last_order_days': last_order_days
        }
        
        # Get favorite products (most purchased)
        product_purchases = {}
        for order in user_orders:
            product_id = order['product_id']
            product_name = order.get('product_name', 'Unknown Product')
            
            if product_id not in product_purchases:
                product_purchases[product_id] = {
                    'name': product_name,
                    'purchase_count': 0,
                    'total_spent': 0.0
                }
            
            product_purchases[product_id]['purchase_count'] += 1
            product_purchases[product_id]['total_spent'] += float(calculate_sale_amount(order))
        
        # Sort by purchase count and get top 6
        favorite_products = sorted(product_purchases.values(), 
                                 key=lambda x: x['purchase_count'], 
                                 reverse=True)[:6]
        
        return render_template('user_detail.html',
                             user=user,
                             user_stats=user_stats,
                             user_orders=user_orders,
                             favorite_products=favorite_products)
    
    except Exception as e:
        print(f"Error in user details: {e}")
        flash('Error loading user details', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/user-pdf/<user_id>')
@admin_required
def admin_user_pdf(user_id):
    """Generate PDF report for a specific user"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's purchase history
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        
        # Calculate statistics
        total_spent = sum(float(calculate_sale_amount(order)) for order in user_orders)
        total_orders = len(user_orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Title
        elements.append(Paragraph(f"User Report: {user.get('name', 'Unknown User')}", title_style))
        elements.append(Spacer(1, 12))
        
        # User Information Table
        user_data = [
            ['Field', 'Value'],
            ['Name', user.get('name', 'N/A')],
            ['Email', user.get('email', 'N/A')],
            ['Mobile', user.get('mobile', 'N/A')],
            ['Join Date', user.get('join_date', 'N/A').strftime('%Y-%m-%d') if user.get('join_date') else 'N/A'],
            ['Total Orders', str(total_orders)],
            ['Total Spent', f"${total_spent:.2f}"],
            ['Average Order Value', f"${avg_order_value:.2f}"]
        ]
        
        user_table = Table(user_data, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(user_table)
        elements.append(Spacer(1, 20))
        
        # Purchase History
        if user_orders:
            elements.append(Paragraph("Purchase History", styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            order_data = [['Date', 'Product', 'Quantity', 'Total', 'Payment Method']]
            for order in user_orders[-10:]:  # Last 10 orders
                order_data.append([
                    order.get('date', 'N/A').strftime('%Y-%m-%d') if order.get('date') else 'N/A',
                    order.get('product_name', 'Unknown')[:30],  # Truncate long names
                    str(order.get('quantity', 0)),
                    f"${float(calculate_sale_amount(order)):.2f}",
                    order.get('payment_method', 'N/A')
                ])
            
            order_table = Table(order_data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 1*inch, 1.5*inch])
            order_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(order_table)
        
        # Build PDF
        doc.build(elements)
        
        # FileResponse
        buffer.seek(0)
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename=user_{user_id}_report.pdf'
        }
        
    except Exception as e:
        print(f"Error generating user PDF: {e}")
        return jsonify({'error': 'Error generating PDF'}), 500

@app.route('/admin/send-targeted-email/<user_id>', methods=['POST'])
@admin_required
def admin_send_targeted_email(user_id):
    """Send targeted email with personalized offers based on user's purchase history"""
    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's purchase history to identify favorite products
        user_orders = list(products_sold.find({'user_id': ObjectId(user_id)}))
        
        if not user_orders:
            return jsonify({'error': 'No purchase history found for this user'}), 400
        
        # Analyze purchase patterns
        product_purchases = {}
        for order in user_orders:
            product_id = order['product_id']
            product_name = order.get('product_name', 'Unknown Product')
            
            if product_id not in product_purchases:
                product_purchases[product_id] = {
                    'name': product_name,
                    'purchase_count': 0,
                    'total_spent': 0.0
                }
            
            product_purchases[product_id]['purchase_count'] += 1
            product_purchases[product_id]['total_spent'] += float(calculate_sale_amount(order))
        
        # Get top 3 most purchased products
        top_products = sorted(product_purchases.values(), 
                            key=lambda x: x['purchase_count'], 
                            reverse=True)[:3]
        
        if not top_products:
            return jsonify({'error': 'No products found in purchase history'}), 400
        
        # Create personalized email content
        most_bought_product = top_products[0]['name']
        total_spent = sum(float(calculate_sale_amount(order)) for order in user_orders)
        
        subject = f"Special 15% Offer Just for You, {user.get('name', 'Valued Customer')}!"
        
        email_content = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Hello {user.get('name', 'Valued Customer')}!</h2>
                
                <p>We've noticed you're one of our valued customers who loves <strong>{most_bought_product}</strong>!</p>
                
                <p>Based on your purchase history, we think you'd be interested in our latest collection. 
                As someone who has spent <strong>${total_spent:.2f}</strong> with us, we want to show our appreciation.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #e74c3c; text-align: center;">🎉 EXCLUSIVE 15% OFF 🎉</h3>
                    <p style="text-align: center; font-size: 18px;">
                        Use code: <strong style="background-color: #fff; padding: 5px 10px; border-radius: 5px;">LOYAL15</strong>
                    </p>
                </div>
                
                <h4>Your Favorite Products:</h4>
                <ul>
        """
        
        for product in top_products:
            email_content += f"<li>{product['name']} - Purchased {product['purchase_count']} times</li>"
        
        email_content += f"""
                </ul>
                
                <p>This exclusive offer is valid for the next 7 days. Don't miss out!</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Shop Now with 15% OFF
                    </a>
                </div>
                
                <p>Thank you for being a loyal customer!</p>
                
                <hr>
                <p style="font-size: 12px; color: #7f8c8d;">
                    This email was sent because you are a valued customer of SalesSense. 
                    If you no longer wish to receive these emails, you can unsubscribe.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('SENDER_EMAIL')
            msg['To'] = user['email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(email_content, 'html'))
            
            server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
            server.starttls()
            server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)
            server.quit()
            
            return jsonify({'success': True, 'message': 'Targeted email sent successfully!'})
            
        except Exception as email_error:
            print(f"Error sending email: {email_error}")
            return jsonify({'error': 'Email could not be sent'}), 500
        
    except Exception as e:
        print(f"Error in targeted email: {e}")
        return jsonify({'error': 'Error processing request'}), 500

@app.route('/admin/products')
@admin_required
def admin_products():
    """Separate page for managing products"""
    try:
        # Get all products for management
        products_data = list(products_update.find())
        for product in products_data:
            product['_id'] = str(product['_id'])
            if 'added_by' in product:
                product['added_by'] = str(product['added_by'])
                
        return render_template('admin_products.html', products=products_data)
    except Exception as e:
        print(f"Error in admin products: {e}")
        return render_template('admin_products.html', products=[])

@app.route('/admin/create-worker', methods=['POST'])
@admin_required
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
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic input validation
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('admin_login.html')
            
        # Check for default admin credentials
        if email == 'admin' and password == 'admin123':
            # Set session with default admin info
            admin = admins.find_one({'email': 'admin'})
            if admin:
                session['admin_id'] = str(admin['_id'])
            else:
                # Create admin user if it doesn't exist
                admin = {
                    'email': 'admin',
                    'password': 'admin123',
                    'name': 'Admin',
                    'role': 'admin',
                    'created_at': datetime.datetime.utcnow()
                }
                result = admins.insert_one(admin)
                session['admin_id'] = str(result.inserted_id)
            
            session['admin_name'] = 'Admin'
            session['login_time'] = datetime.datetime.utcnow().timestamp()
            session['last_activity'] = datetime.datetime.utcnow().timestamp()
            
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        flash('Invalid credentials', 'error')
        return render_template('admin_login.html')
    
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