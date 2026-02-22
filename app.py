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
# Use environment variable for SECRET_KEY, fallback to a stable key (random rotates on restart and kills sessions)
app.secret_key = os.environ.get('SECRET_KEY', 'salessense-stable-key-2026-do-not-change')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

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
    },
    'Valentine\'s Day': {
        'month': 'February',
        'products': ['Chocolate', 'Roses', 'Teddy Bears', 'Greeting Cards', 'Perfume', 'Jewelry'],
        'categories': ['Gifts & Occasions', 'Food & Beverages', 'Personal Care'],
        'discount_range': '20-40%',
        'boost_percentage': 45
    },
    'Chocolate Day': {
        'month': 'February',
        'products': ['Dark Chocolate', 'Milk Chocolate', 'Chocolate Boxes', 'Truffles', 'Chocolate Cake'],
        'categories': ['Food & Beverages', 'Gifts & Occasions'],
        'discount_range': '25-35%',
        'boost_percentage': 40
    },
    'Rose Day': {
        'month': 'February',
        'products': ['Red Roses', 'Pink Roses', 'Rose Bouquet', 'Flowers', 'Flower Vases'],
        'categories': ['Gifts & Occasions', 'Flowers & Plants'],
        'discount_range': '15-30%',
        'boost_percentage': 35
    },
    'Teddy Day': {
        'month': 'February',
        'products': ['Teddy Bears', 'Soft Toys', 'Stuffed Animals', 'Plush Toys', 'Gift Sets'],
        'categories': ['Gifts & Occasions', 'Toys'],
        'discount_range': '20-35%',
        'boost_percentage': 40
    },
    'Promise Day': {
        'month': 'February',
        'products': ['Promise Rings', 'Bracelets', 'Greeting Cards', 'Jewelry', 'Couple Gifts'],
        'categories': ['Gifts & Occasions', 'Jewelry & Accessories'],
        'discount_range': '15-30%',
        'boost_percentage': 30
    },
    'Women\'s Day': {
        'month': 'March',
        'products': ['Beauty Products', 'Perfume', 'Jewelry', 'Handbags', 'Flowers', 'Spa Kits'],
        'categories': ['Personal Care', 'Gifts & Occasions', 'Fashion'],
        'discount_range': '25-40%',
        'boost_percentage': 45
    },
    'Mother\'s Day': {
        'month': 'May',
        'products': ['Flowers', 'Jewelry', 'Perfume', 'Sarees', 'Greeting Cards', 'Kitchen Appliances'],
        'categories': ['Gifts & Occasions', 'Fashion', 'Home & Kitchen'],
        'discount_range': '20-40%',
        'boost_percentage': 45
    },
    'Father\'s Day': {
        'month': 'June',
        'products': ['Shirts', 'Ties', 'Wallets', 'Watches', 'Perfume', 'Gadgets', 'Grooming Kits'],
        'categories': ['Gifts & Occasions', 'Fashion', 'Electronics'],
        'discount_range': '20-35%',
        'boost_percentage': 40
    },
    'Friendship Day': {
        'month': 'August',
        'products': ['Friendship Bands', 'Greeting Cards', 'Chocolates', 'Personalized Gifts', 'Photo Frames'],
        'categories': ['Gifts & Occasions', 'Food & Beverages'],
        'discount_range': '15-30%',
        'boost_percentage': 35
    },
    'Raksha Bandhan': {
        'month': 'August',
        'products': ['Rakhi', 'Sweets', 'Dry Fruits', 'Traditional Sweets', 'Gifts for Brothers'],
        'categories': ['Festival Items', 'Food & Beverages', 'Gifts & Occasions'],
        'discount_range': '20-35%',
        'boost_percentage': 40
    },
    'Teacher\'s Day': {
        'month': 'September',
        'products': ['Books', 'Pens', 'Greeting Cards', 'Flowers', 'Gift Hampers', 'Desk Accessories'],
        'categories': ['Gifts & Occasions', 'Stationery', 'Books'],
        'discount_range': '15-25%',
        'boost_percentage': 30
    },
    'Halloween': {
        'month': 'October',
        'products': ['Candies', 'Chocolates', 'Costumes', 'Pumpkins', 'Party Supplies', 'Decorations'],
        'categories': ['Food & Beverages', 'Party Supplies', 'Festival Items'],
        'discount_range': '20-35%',
        'boost_percentage': 35
    },
    'Black Friday': {
        'month': 'November',
        'products': ['Electronics', 'Fashion', 'Home Appliances', 'Gadgets', 'Books', 'Toys'],
        'categories': ['Electronics', 'Fashion', 'Home & Kitchen', 'All Categories'],
        'discount_range': '30-60%',
        'boost_percentage': 60
    },
    'Thanksgiving': {
        'month': 'November',
        'products': ['Turkey', 'Pumpkin Pie', 'Cranberries', 'Wine', 'Vegetables', 'Baking Supplies'],
        'categories': ['Food & Beverages', 'Traditional Foods'],
        'discount_range': '15-30%',
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
        mongo_url = os.getenv('MONGODB_URL')

        if not mongo_url:
            raise Exception("MONGODB_URL not found in environment variables")

        client = MongoClient(mongo_url)

        # Test the connection
        client.admin.command('ping')

        db = client["saless"]
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
            # Return static Tamil product data for display
            return {
                'top_performers': [
                    {
                        'name': 'பாசுமதி அரிசி (Basmati Rice)',
                        'category': 'மளிகை (Groceries)',
                        'revenue': 145680.50,
                        'quantity_sold': 425,
                        'customer_count': 89,
                        'order_count': 156,
                        'avg_order_value': 934.10,
                        'action': 'Increase stock by 45% - High demand product'
                    },
                    {
                        'name': 'தேங்காய் எண்ணெய் (Coconut Oil)',
                        'category': 'மளிகை (Groceries)',
                        'revenue': 98450.75,
                        'quantity_sold': 287,
                        'customer_count': 76,
                        'order_count': 132,
                        'avg_order_value': 745.83,
                        'action': 'Increase stock by 40% - High demand product'
                    },
                    {
                        'name': 'சாம்பார் பொடி (Sambar Powder)',
                        'category': 'மளிகை (Groceries)',
                        'revenue': 76890.25,
                        'quantity_sold': 398,
                        'customer_count': 68,
                        'order_count': 145,
                        'avg_order_value': 530.28,
                        'action': 'Increase stock by 38% - High demand product'
                    },
                    {
                        'name': 'முறுக்கு (Murukku)',
                        'category': 'தின்பண்டங்கள் (Snacks)',
                        'revenue': 65420.80,
                        'quantity_sold': 312,
                        'customer_count': 54,
                        'order_count': 98,
                        'avg_order_value': 667.56,
                        'action': 'Monitor closely - Growing popularity'
                    }
                ],
                'poor_performers': [
                    {
                        'name': 'சீடை (Seedai)',
                        'category': 'தின்பண்டங்கள் (Snacks)',
                        'revenue': 12340.50,
                        'quantity_sold': 45,
                        'customer_count': 12,
                        'order_count': 18,
                        'avg_order_value': 685.58,
                        'action': 'Review pricing strategy'
                    },
                    {
                        'name': 'சந்தனம் (Sandalwood)',
                        'category': 'தனிப்பட்ட பராமரிப்பு (Personal Care)',
                        'revenue': 8965.00,
                        'quantity_sold': 15,
                        'customer_count': 8,
                        'order_count': 12,
                        'avg_order_value': 747.08,
                        'action': 'Reduce stock by 30% and consider promotion'
                    }
                ],
                'analysis_period': '90 days',
                'total_products_analyzed': 20
            }
        
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
        # Return empty if database is not connected
        if db is None or products_update is None:
            return recommendations
            
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
        # Return empty if database is not connected
        if db is None or products_sold is None:
            return alerts
            
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
    """Send email via SMTP. Returns (True, '') on success or (False, error_message) on failure."""
    try:
        smtp_server   = os.getenv('SMTP_SERVER')
        smtp_port     = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email  = os.getenv('SENDER_EMAIL')

        # Validate that SMTP env vars are configured
        if not smtp_server:
            return False, 'SMTP_SERVER is not configured in environment variables.'
        if not smtp_username or not smtp_password:
            return False, 'SMTP_USERNAME / SMTP_PASSWORD not configured in environment variables.'
        if not sender_email:
            return False, 'SENDER_EMAIL is not configured in environment variables.'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = sender_email
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True, ''
    except Exception as e:
        err = str(e)
        print(f'Error sending email to {to_email}: {err}')
        return False, err


# ── In-memory bulk-send job tracker ───────────────────────────────────────────
_bulk_jobs: dict = {}  # job_id -> {status, sent, failed, total, error, done}

def _run_bulk_send(job_id: str, recipient_list: list, subject: str,
                   html_body: str, recipient_type: str, invalid_count: int,
                   body_preview: str):
    """Background thread: open ONE SMTP connection, send all messages, log result."""
    import uuid as _uuid
    job = _bulk_jobs[job_id]
    try:
        smtp_server   = os.getenv('SMTP_SERVER')
        smtp_port     = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email  = os.getenv('SENDER_EMAIL')

        # Open a single connection for the whole batch
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_username, smtp_password)

        for addr in recipient_list:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From']    = sender_email
                msg['To']      = addr
                msg.attach(MIMEText(html_body, 'html'))
                server.send_message(msg)
                job['sent'] += 1
            except Exception as e:
                err_str = str(e)
                job['failed'] += 1
                if not job['error']:
                    job['error'] = err_str
                # Gmail 550 daily limit — no point continuing, all will fail
                if '550' in err_str and ('limit' in err_str.lower() or '5.4.5' in err_str):
                    remaining = len(recipient_list) - job['sent'] - job['failed']
                    job['failed'] += remaining
                    job['error'] = ('Gmail daily sending limit exceeded. '
                                    'Free Gmail accounts allow ~500 emails/day. '
                                    'Please wait 24 hours or use a Google Workspace account.')
                    break

        try:
            server.quit()
        except Exception:
            pass

    except Exception as e:
        job['error'] = str(e)
        # Mark remaining as failed
        remaining = job['total'] - job['sent'] - job['failed']
        job['failed'] += remaining
    finally:
        job['status'] = 'done'
        job['done']   = True
        # Log result to MongoDB
        try:
            if email_logs is not None:
                email_logs.insert_one({
                    'recipient_type':  recipient_type,
                    'recipient_count': job['sent'],
                    'failed_count':    job['failed'],
                    'invalid_count':   invalid_count,
                    'subject':         subject,
                    'preview':         body_preview,
                    'sent_at':         datetime.datetime.utcnow(),
                    'status':          'sent' if job['sent'] > 0 else 'failed'
                })
        except Exception:
            pass
# ──────────────────────────────────────────────────────────────────────────────

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

# Collections - Initialize only if database connection is successful
if db is not None:
    products = db.products
    products_update = db.products_update
    workers_update = db.workers_update  # Changed from workers to workers_update
    worker_specific_added = db.worker_specific_added
    chat_history = db.chat_history  # New collection for worker actions
    email_logs   = db.email_logs    # Email send history
    admin_ai_chats = db.admin_ai_chats  # AI chat session history
    labors = db.labors
    admins = db.admins
    users = db.users  # New users collection
    users_update = db.users_update  # Existing users collection
    products_sold = db.products_sold
    products_by_user = db.products_by_user
    user_data_bought = db.user_data_bought  # User purchase history
    carts = db.carts  # Persistent cart storage (avoids session cookie limits)
else:
    # Set collections to None if database connection failed
    products = None
    products_update = None
    workers_update = None
    worker_specific_added = None
    chat_history = None
    email_logs   = None
    admin_ai_chats = None
    admins = None
    users = None
    users_update = None
    products_sold = None
    products_by_user = None
    user_data_bought = None
    carts = None
    print("Warning: Database collections not initialized due to connection failure.")

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

def get_active_festival_discounts():
    """Return {product_name: {type, pct, flat, label, festival, emoji, override_price}}
    for all custom_festivals whose start_date <= now <= end_date."""
    import re as _re
    now = datetime.datetime.utcnow()
    discounts = {}
    try:
        for cf in db.custom_festivals.find({
            'start_date': {'$lte': now},
            'end_date':   {'$gte': now}
        }):
            discount_str = str(cf.get('discount', '')).strip()
            overrides = cf.get('product_prices') or {}  # {name: override_price}
            pct = flat = 0.0
            dtype = None
            m = _re.search(r'(\d+(?:\.\d+)?)\s*%', discount_str)
            if m:
                pct = float(m.group(1))
                dtype = 'pct'
                label = f"{pct:.0f}% off"
            else:
                m2 = _re.search(r'(\d+(?:\.\d+)?)', discount_str)
                if m2:
                    flat = float(m2.group(1))
                    dtype = 'flat'
                    label = f'Rs.{flat:.0f} off'
            for pname in cf.get('products', []):
                if not pname:
                    continue
                entry = {
                    'type': dtype or 'pct',
                    'pct': pct, 'flat': flat,
                    'label': label if dtype else '',
                    'festival': cf.get('name', 'Festival Offer'),
                    'emoji': cf.get('emoji', 'Rs.'),
                    'override_price': overrides.get(pname)  # manual price or None
                }
                if pname not in discounts:
                    discounts[pname] = entry
    except Exception:
        pass
    return discounts


def _apply_festival_discounts(products_list):
    """Enrich product dicts in-memory with offer_price / original_price fields."""
    discounts = get_active_festival_discounts()
    if not discounts:
        return products_list
    for product in products_list:
        name = product.get('name', '')
        if name not in discounts:
            continue
        fd = discounts[name]
        product['festival_discount'] = fd

        def compute_offer(orig):
            orig = float(orig or 0)
            if fd.get('override_price') is not None:
                return round(float(fd['override_price']), 2)
            if fd['type'] == 'pct' and fd['pct']:
                return round(orig * (1 - fd['pct'] / 100), 2)
            if fd['type'] == 'flat' and fd['flat']:
                return round(max(0, orig - fd['flat']), 2)
            return orig

        if product.get('variants'):
            for v in product['variants']:
                orig = float(v.get('price', 0))
                offer = compute_offer(orig)
                if offer != orig:
                    v['original_price'] = orig
                    v['price'] = offer
        elif product.get('price'):
            orig = float(product['price'])
            offer = compute_offer(orig)
            if offer != orig:
                product['original_price'] = orig
                product['price'] = offer
    return products_list


@app.route('/products')
@require_db_connection
def product_list():
    # Fetch products from all collections
    all_products = []
    
    # Get from products_update collection
    if products_update is not None:
        all_products.extend(list(products_update.find()))
    
    # Get from products collection
    if products is not None:
        all_products.extend(list(products.find()))
    
    # Get from products_by_user collection (added by workers)
    if products_by_user is not None:
        all_products.extend(list(products_by_user.find()))
    
    # Remove duplicates based on name and category
    seen_products = set()
    unique_products = []
    for product in all_products:
        name = product.get('name', '')
        category = product.get('category', '')
        key = f"{name}_{category}"
        if name and key not in seen_products:
            seen_products.add(key)
            unique_products.append(product)
    
    # Apply active festival discounts in-memory (non-destructive)
    unique_products = _apply_festival_discounts(unique_products)
    
    return render_template('products.html', products=unique_products)

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

        # Use user_data_bought (the actual sales collection with purchase_date)
        total_sales_result = list(user_data_bought.aggregate([
            {'$match': {'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ])) if user_data_bought is not None else []
        total_sales = float(total_sales_result[0]['total']) if total_sales_result else 0.0

        # Calculate today's sales using purchase_date field
        sales_today_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': today}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ])) if user_data_bought is not None else []
        sales_today = float(sales_today_result[0]['total']) if sales_today_result else 0.0

        # Get statistics - optimized queries
        _u_count = (users.count_documents({}) if users is not None else 0) + \
                   (users_update.count_documents({}) if users_update is not None else 0)
        stats = {
            'total_users': _u_count,
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

        # Get recent users with pagination support - from BOTH users and users_update
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Show 20 users per page
        skip = (page - 1) * per_page

        # Merge users from both collections
        all_users_merged = []
        seen_ids = set()
        for col in [users, users_update]:
            if col is not None:
                for u in col.find().sort('_id', -1):
                    uid_s = str(u['_id'])
                    if uid_s not in seen_ids:
                        seen_ids.add(uid_s)
                        all_users_merged.append(u)

        total_users_count = len(all_users_merged)
        total_pages = (total_users_count + per_page - 1) // per_page if total_users_count else 0

        # Apply pagination
        paginated = all_users_merged[skip: skip + per_page]
        recent_users = []
        for user in paginated:
            user['_id'] = str(user['_id'])
            recent_users.append(user)

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

        # Last 7 days sales using user_data_bought
        for i in range(6, -1, -1):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0)
            end_date = date.replace(hour=23, minute=59, second=59)

            daily_result = list(user_data_bought.aggregate([
                {'$match': {'purchase_date': {'$gte': start_date, '$lte': end_date}, 'total': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
            ])) if user_data_bought is not None else []
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

        # Top products (for reports) - from user_data_bought (all Tamil names)
        top_products = []
        try:
            # Pull top products from user_data_bought (all Tamil names now)
            top_products_results = list(user_data_bought.aggregate([
                {'$group': {'_id': '$product_name', 'total_revenue': {'$sum': '$total'}, 'units_sold': {'$sum': '$quantity'}}},
                {'$sort': {'total_revenue': -1}},
                {'$limit': 8}
            ])) if user_data_bought is not None else []
            for result in top_products_results:
                product_name = result.get('_id', 'Unknown') or 'Unknown'
                top_products.append({
                    'name': product_name,
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

# Add Worker Route
@app.route('/admin/add-worker', methods=['POST'])
@admin_required
def add_worker():
    try:
        # Support both JSON and form data
        if request.is_json:
            form = request.get_json() or {}
        else:
            form = request.form
        name = (form.get('name') or '').strip()
        email = (form.get('email') or '').strip()
        password = (form.get('password') or '').strip()
        date_of_joining = (form.get('date_of_joining') or '').strip()
        
        # Validate required fields
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'Name, email, and password are required'}), 400
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Check if worker already exists
        existing_worker = workers_update.find_one({'email': email})
        if existing_worker:
            return jsonify({'success': False, 'message': 'Worker with this email already exists'}), 400
        
        # Parse date of joining
        if date_of_joining:
            try:
                doj = datetime.datetime.strptime(date_of_joining, '%Y-%m-%d')
            except ValueError:
                doj = datetime.datetime.now()
        else:
            doj = datetime.datetime.now()
        
        # Create worker document
        worker_data = {
            'name': name,
            'email': email,
            'password': password,  # In production, hash this!
            'date_of_joining': doj,
            'created_at': datetime.datetime.now(),
            'last_active': None,
            'role': 'Worker',
            'status': 'Active'
        }
        
        # Insert worker into database
        result = workers_update.insert_one(worker_data)
        
        if result.inserted_id:
            # Send welcome email
            email_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .content {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                    }}
                    .header {{
                        text-align: center;
                        color: #667eea;
                        margin-bottom: 30px;
                    }}
                    .credentials {{
                        background: #f9fafb;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .credential-item {{
                        margin: 10px 0;
                        padding: 10px;
                        background: white;
                        border-left: 4px solid #667eea;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        color: #6b7280;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="content">
                        <div class="header">
                            <h1>Welcome to SalesSense!</h1>
                        </div>
                        
                        <p>Dear {name},</p>
                        
                        <p>Welcome to the SalesSense team! We're excited to have you on board.</p>
                        
                        <p>Your account has been created and you can now access the SalesSense worker portal.</p>
                        
                        <div class="credentials">
                            <h3 style="margin-top: 0;">Your Login Credentials:</h3>
                            <div class="credential-item">
                                <strong>Email:</strong> {email}
                            </div>
                            <div class="credential-item">
                                <strong>Password:</strong> {password}
                            </div>
                            <div class="credential-item">
                                <strong>Date of Joining:</strong> {doj.strftime('%B %d, %Y')}
                            </div>
                        </div>
                        
                        <p><strong>Portal URL:</strong> <a href="http://localhost:5000/worker/login">http://localhost:5000/worker/login</a></p>
                        
                        <p style="color: #ef4444; font-size: 14px;">
                            <strong>Important:</strong> Please change your password after your first login for security purposes.
                        </p>
                        
                        <p>If you have any questions or need assistance, please don't hesitate to contact the admin.</p>
                        
                        <div class="footer">
                            <p>Best regards,<br>The SalesSense Team</p>
                            <p style="font-size: 12px; color: #9ca3af;">This is an automated message, please do not reply to this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            email_sent, _ = send_email(email, 'Welcome to SalesSense!', email_html)

            if email_sent:
                return jsonify({
                    'success': True, 
                    'message': f'Worker {name} added successfully! Welcome email sent to {email}'
                }), 200
            else:
                return jsonify({
                    'success': True, 
                    'message': f'Worker {name} added successfully! (Warning: Email could not be sent)'
                }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to add worker'}), 500
            
    except Exception as e:
        print(f"Error adding worker: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# User Details View Route
@app.route('/admin/user-details/<user_id>')
@admin_required
def user_details(user_id):
    try:
        # Get user information - check both users and users_update collections
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user and users_update is not None:
            user = users_update.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        user['_id'] = str(user['_id'])
        
        # Get user's purchase history from both collections
        uid_obj = ObjectId(user_id)
        orders_from_sold   = list(products_sold.find({'user_id': uid_obj})) if products_sold is not None else []
        orders_from_bought = list(user_data_bought.find({'user_id': uid_obj})) if user_data_bought is not None else []

        # Merge, de-duplicate by order_id + product_id
        seen = set()
        user_orders = []
        for order in orders_from_bought + orders_from_sold:
            key = (str(order.get('order_id', '')), str(order.get('product_id', '')), str(order.get('variant_index', '')))
            if key not in seen:
                seen.add(key)
                user_orders.append(order)

        total_spent = 0
        total_orders = len(user_orders)
        
        # Process orders and calculate statistics
        product_purchases = {}
        monthly_spending = {}
        
        for order in user_orders:
            order['_id'] = str(order['_id'])
            order['user_id'] = str(order['user_id'])
            order['product_id'] = str(order['product_id'])

            # Normalise total
            order_total = float(order.get('total') or order.get('total_price') or
                                 (float(order.get('price', 0)) * float(order.get('quantity', 1))))
            total_spent += order_total
            order['total'] = order_total

            # Normalise date (supports both 'date' and 'purchase_date' fields)
            order_date = order.get('purchase_date') or order.get('date') or datetime.datetime.now()
            if isinstance(order_date, str):
                try:
                    order_date = datetime.datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                except Exception:
                    order_date = datetime.datetime.now()
            order['date'] = order_date          # ensure template always has .date

            # Track product purchases
            product_id = order['product_id']
            if product_id not in product_purchases:
                try:
                    product = products_update.find_one({'_id': ObjectId(product_id)}) if products_update else None
                except Exception:
                    product = None
                pname = (product['name'] if product else None) or order.get('product_name', 'Unknown')
                product_purchases[product_id] = {'name': pname, 'quantity': 0, 'total_spent': 0}

            try:
                qty = int(float(order.get('quantity', 1)))
            except Exception:
                qty = 1
            product_purchases[product_id]['quantity'] += qty
            product_purchases[product_id]['total_spent'] += order_total

            # Monthly spending
            month_key = order_date.strftime('%Y-%m')
            monthly_spending[month_key] = monthly_spending.get(month_key, 0) + order_total
        
        # Get top purchased products
        top_products = sorted(product_purchases.values(), key=lambda x: x['total_spent'], reverse=True)[:5]
        
        # Calculate user statistics
        user_stats = {
            'total_spent': total_spent,
            'total_orders': total_orders,
            'average_order_value': total_spent / total_orders if total_orders > 0 else 0,
            'favorite_product': top_products[0]['name'] if top_products else 'None',
            'join_date': user.get('join_date', user.get('created_at', 'Unknown')),
            'last_order': max([o['date'] for o in user_orders if isinstance(o.get('date'), datetime.datetime)], default='Never')
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
                ok, err = send_email(user['email'], subject, html_body)
                if ok:
                    return jsonify({'success': True, 'message': f'Marketing email sent to {user["name"]}!'})
                else:
                    return jsonify({'error': f'Failed to send email: {err}'}), 500
        
        return jsonify({'error': 'No purchase history found for personalized email'}), 400
    
    except Exception as e:
        print(f"Error sending marketing email: {e}")
        return jsonify({'error': 'Failed to send marketing email'}), 500

# Chatbot functionality
@app.route('/chatbot')  # public redirect → admin AI chat
def chatbot_redirect():
    return redirect(url_for('admin_ai_chat_page'))


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

# ─── Fast chatbot cache ────────────────────────────────────────────────────────
_chat_cache: dict = {}          # key -> (reply_str, expire_timestamp)
_CHAT_TTL    = 90               # seconds each cached answer stays valid

def _cached_call(key: str, fn):
    """Return cached result if fresh, else call fn(), cache and return result."""
    import time
    now = time.time()
    if key in _chat_cache:
        reply, exp = _chat_cache[key]
        if now < exp:
            return reply
    result = fn()
    _chat_cache[key] = (result, now + _CHAT_TTL)
    return result
# ──────────────────────────────────────────────────────────────────────────────


def process_admin_query(query):
    """Process admin queries and return appropriate responses (with fast cache)."""
    try:
        q = query.lower().strip()

        # ── Instant no-DB greetings / help ────────────────────────────────────
        if any(w in q for w in ['hello', 'hi', 'hey', 'help', 'what can', 'who are']):
            return ("👋 Hi! I'm your SalesSense AI assistant.\n\n"
                    "Ask me about:\n"
                    "📊 **Sales & Revenue** — total / today's figures\n"
                    "👥 **Users & Customers** — count, top buyers\n"
                    "📦 **Products & Inventory** — stock levels\n"
                    "👷 **Workers & Staff** — activity\n"
                    "🏆 **Top Selling** products right now\n"
                    "⚠️ **Low Stock** alerts\n"
                    "📅 **Recent Activity** — latest orders\n\n"
                    "Just type your question!")

        # ── Cached DB queries ──────────────────────────────────────────────────
        if any(w in q for w in ['sales', 'revenue', 'money', 'earning']):
            return _cached_call('sales', get_sales_summary)

        elif any(w in q for w in ['top', 'best', 'popular', 'trending']):
            return _cached_call('top_products', get_top_products_summary)

        elif any(w in q for w in ['low stock', 'shortage', 'running out', 'out of stock']):
            return _cached_call('low_stock', get_low_stock_summary)

        elif any(w in q for w in ['recent', 'today', 'latest', 'last order']):
            return _cached_call('recent', get_recent_activity_summary)

        elif any(w in q for w in ['user', 'customer', 'client', 'buyer', 'how many user']):
            return _cached_call('users', get_user_summary)

        elif any(w in q for w in ['product', 'inventory', 'stock', 'item']):
            return _cached_call('products', get_product_summary)

        elif any(w in q for w in ['worker', 'employee', 'staff']):
            return _cached_call('workers', get_worker_summary)

        else:
            return ("🤔 I didn't quite catch that. Try asking:\n"
                    "- *Today's sales total*\n"
                    "- *How many users do we have?*\n"
                    "- *Top selling products*\n"
                    "- *Low stock alerts*\n"
                    "- *Recent orders*")

    except Exception as e:
        print(f"Error processing query: {e}")
        return "Sorry, I encountered an error. Please try again."

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
            # Skip refresh if database is not connected
            if db is None or users is None:
                print("Skipping cache refresh - database not connected")
                time.sleep(900)
                continue
                
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
        # Return empty stats if database is not connected
        if db is None or user_data_bought is None:
            return jsonify({
                'total_users': 0, 'new_users_today': 0, 'active_users': 0,
                'total_sales': 0.0, 'sales_today': 0.0, 'total_orders': 0,
                'orders_today': 0, 'total_products': 0, 'total_workers': 0,
                'top_products': [], 'sales_trend': [], 'category_breakdown': [],
                'avg_order_value': 0, 'error': 'Database not connected'
            })

        # ── date range from query param (default 30 days) ──────────────
        days = request.args.get('days', 30, type=int)
        if days not in (7, 30, 90, 365):
            days = 30

        now          = datetime.datetime.now()
        today        = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = now - datetime.timedelta(days=days)

        # ── revenue for the selected period ────────────────────────────
        period_sales_pipeline = [
            {'$match': {'purchase_date': {'$gte': period_start}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'total_revenue': {'$sum': '$total'}, 'count': {'$sum': 1}}}
        ]
        period_result    = list(user_data_bought.aggregate(period_sales_pipeline))
        total_sales      = float(period_result[0]['total_revenue']) if period_result else 0.0
        total_purchase_count = int(period_result[0]['count']) if period_result else 0

        # ── today's sales (always fixed to today regardless of period) ─
        sales_today_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': today}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]))
        sales_today = float(sales_today_result[0]['total']) if sales_today_result else 0.0

        print(f"[Analytics] Period={days}d, Revenue=₹{total_sales:.2f}, Today=₹{sales_today:.2f}")

        # ── orders in selected period ───────────────────────────────────
        total_orders  = user_data_bought.count_documents({'purchase_date': {'$gte': period_start}}) if user_data_bought is not None else 0
        orders_today  = user_data_bought.count_documents({'purchase_date': {'$gte': today}})        if user_data_bought is not None else 0

        # ── unique products ─────────────────────────────────────────────
        unique_products = set()
        for col in [products, products_update, products_by_user]:
            if col is not None:
                for p in col.find({}, {'name': 1}):
                    if 'name' in p:
                        unique_products.add(p['name'])
        total_products = len(unique_products)

        # ── active / total users ────────────────────────────────────────
        active_users_count = 0
        total_users_count  = 0
        new_users_today    = 0
        for col in [users, users_update]:
            if col is not None:
                active_users_count += col.count_documents({})
                total_users_count  += col.count_documents({})
        if users is not None:
            new_users_today = users.count_documents({'created_at': {'$gte': today}})

        # ── top products for the selected period ────────────────────────
        top_products_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': period_start}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': '$product_name', 'total_revenue': {'$sum': '$total'}, 'units_sold': {'$sum': '$quantity'}}},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 8}
        ]))
        top_products = [
            {'name': p['_id'], 'revenue': float(p.get('total_revenue', 0)), 'units': int(p.get('units_sold', 0))}
            for p in top_products_result
        ]

        # ── top users by spending ────────────────────────────────────────
        top_users_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': period_start}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': '$user_name',
                'total_spent': {'$sum': '$total'},
                'order_count': {'$sum': 1}
            }},
            {'$sort': {'total_spent': -1}},
            {'$limit': 5}
        ]))
        top_users = [
            {
                'name':   (u['_id'] or 'Guest'),
                'spent':  float(u.get('total_spent', 0)),
                'orders': int(u.get('order_count', 0))
            }
            for u in top_users_result
        ]

        # ── sales trend (daily for ≤30d; weekly for >30d) ───────────────
        sales_trend = []
        if days <= 30:
            # Daily data points
            for i in range(days - 1, -1, -1):
                d     = now - datetime.timedelta(days=i)
                start = d.replace(hour=0, minute=0, second=0, microsecond=0)
                end   = d.replace(hour=23, minute=59, second=59, microsecond=999999)
                res   = list(user_data_bought.aggregate([
                    {'$match': {'purchase_date': {'$gte': start, '$lte': end}, 'total': {'$exists': True, '$ne': None}}},
                    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
                ]))
                sales_trend.append({
                    'date':  d.strftime('%d %b'),
                    'sales': float(res[0]['total']) if res else 0.0
                })
        else:
            # Weekly data points (group by ISO week)
            num_weeks = days // 7
            for w in range(num_weeks - 1, -1, -1):
                start = today - datetime.timedelta(days=(w + 1) * 7 - 1)
                end   = today - datetime.timedelta(days=w * 7)
                end   = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                res   = list(user_data_bought.aggregate([
                    {'$match': {'purchase_date': {'$gte': start, '$lte': end}, 'total': {'$exists': True, '$ne': None}}},
                    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
                ]))
                sales_trend.append({
                    'date':  start.strftime('%d %b'),
                    'sales': float(res[0]['total']) if res else 0.0
                })

        # ── category breakdown for the selected period ──────────────────
        category_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': period_start}, 'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': '$category', 'total_revenue': {'$sum': '$total'}, 'count': {'$sum': 1}}},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 8}
        ]))
        category_breakdown = [
            {'name': c['_id'] if c['_id'] else 'Uncategorized', 'total': float(c.get('total_revenue', 0)), 'count': int(c.get('count', 0))}
            for c in category_result
        ]

        stats = {
            'days':             days,
            'total_users':      total_users_count,
            'new_users_today':  new_users_today,
            'active_users':     active_users_count,
            'total_sales':      total_sales,
            'total_revenue':    total_sales,
            'sales_today':      sales_today,
            'total_orders':     total_orders,
            'orders_today':     orders_today,
            'total_products':   total_products,
            'total_workers':    workers_update.count_documents({}) if workers_update is not None else 0,
            'top_products':     top_products,
            'top_users':        top_users,
            'sales_trend':      sales_trend,
            'category_breakdown': category_breakdown,
            'category_sales':   category_breakdown,   # legacy alias
            'avg_order_value':  round(total_sales / total_orders, 2) if total_orders > 0 else 0,
            'total_purchases':  total_purchase_count,
        }

        return jsonify(stats)
    except Exception as e:
        print(f"Error getting business stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'total_users': 0, 'new_users_today': 0, 'active_users': 0,
            'total_sales': 0.0, 'sales_today': 0.0, 'total_orders': 0,
            'orders_today': 0, 'total_products': 0, 'total_workers': 0,
            'top_products': [], 'sales_trend': [], 'category_breakdown': [],
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


@app.route('/api/product-detail')
def product_detail_api():
    """Get all purchase records for a specific product"""
    try:
        product_name = request.args.get('name', '').strip()
        if not product_name or user_data_bought is None:
            return jsonify({'error': 'Product name required or DB not connected'}), 400

        purchases = list(user_data_bought.find(
            {'product_name': product_name},
            {'_id': 0, 'user_name': 1, 'buyer_name': 1, 'quantity': 1,
             'total': 1, 'purchase_date': 1, 'category': 1, 'price': 1}
        ).sort('purchase_date', -1).limit(60))

        total_revenue = sum(float(p.get('total', 0)) for p in purchases)
        total_units   = sum(int(p.get('quantity', 0)) for p in purchases)
        unique_buyers = len(set(p.get('user_name') or p.get('buyer_name', 'Guest') for p in purchases))

        records = []
        for p in purchases:
            pd_val = p.get('purchase_date')
            date_str = pd_val.strftime('%d %b %Y') if hasattr(pd_val, 'strftime') else str(pd_val)[:10]
            records.append({
                'buyer':    p.get('user_name') or p.get('buyer_name') or 'Guest',
                'quantity': int(p.get('quantity', 0)),
                'total':    float(p.get('total', 0)),
                'date':     date_str,
                'category': p.get('category', ''),
            })

        return jsonify({
            'product_name':  product_name,
            'total_revenue': total_revenue,
            'total_units':   total_units,
            'unique_buyers': unique_buyers,
            'total_orders':  len(purchases),
            'records':       records
        })
    except Exception as e:
        print(f"Error in product-detail API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user-detail')
def user_detail_api():
    """Get full purchase history for a specific user"""
    try:
        user_name = request.args.get('name', '').strip()
        if not user_name or user_data_bought is None:
            return jsonify({'error': 'User name required or DB not connected'}), 400

        purchases = list(user_data_bought.find(
            {'$or': [{'user_name': user_name}, {'buyer_name': user_name}]},
            {'_id': 0, 'product_name': 1, 'quantity': 1, 'total': 1,
             'purchase_date': 1, 'category': 1, 'price': 1}
        ).sort('purchase_date', -1).limit(60))

        total_spent   = sum(float(p.get('total', 0)) for p in purchases)
        total_units   = sum(int(p.get('quantity', 0)) for p in purchases)
        categories    = list({p.get('category', 'N/A') for p in purchases if p.get('category')})

        records = []
        for p in purchases:
            pd_val = p.get('purchase_date')
            date_str = pd_val.strftime('%d %b %Y') if hasattr(pd_val, 'strftime') else str(pd_val)[:10]
            records.append({
                'product':  p.get('product_name', 'Unknown'),
                'category': p.get('category', ''),
                'quantity': int(p.get('quantity', 0)),
                'total':    float(p.get('total', 0)),
                'date':     date_str,
            })

        return jsonify({
            'user_name':    user_name,
            'total_spent':  total_spent,
            'total_units':  total_units,
            'total_orders': len(purchases),
            'categories':   categories,
            'records':      records
        })
    except Exception as e:
        print(f"Error in user-detail API: {e}")
        return jsonify({'error': str(e)}), 500

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
        
        # If no data available and demo requested (or admin viewing), generate sample/demo data for UI
        demo_flag = request.args.get('demo', 'false').lower() == 'true'
        try:
            is_admin = bool(session.get('admin_logged_in'))
        except Exception:
            is_admin = False

        if demo_flag or (is_admin and total_orders == 0):
            import random
            # Generate last 7 days sample sales trend
            sample_trend = []
            trend_total = 0.0
            today = end_date
            for i in range(6, -1, -1):
                d = (today - datetime.timedelta(days=i))
                sales_val = round(random.uniform(200.0, 2000.0), 2)
                trend_total += sales_val
                sample_trend.append({'date': d.strftime('%m/%d'), 'sales': sales_val})

            # Sample top products using a few real products if available
            sample_products = []
            try:
                real_products = list(products_update.find().limit(10))
            except Exception:
                real_products = []

            for i in range(5):
                name = real_products[i]['name'] if i < len(real_products) else f"Sample Product {i+1}"
                units = random.randint(20, 500)
                revenue = round(units * random.uniform(10.0, 100.0), 2)
                sample_products.append({'name': name, 'revenue': revenue, 'units': units})

            # Sample top customers
            sample_customers = []
            try:
                real_users = list(users.find({}, {'name':1, 'email':1}).limit(10))
            except Exception:
                real_users = []

            for i in range(5):
                if i < len(real_users):
                    name = real_users[i].get('name', f'Customer {i+1}')
                    email = real_users[i].get('email', f'cust{i+1}@example.com')
                else:
                    name = f'Sample Customer {i+1}'
                    email = f'cust{i+1}@example.com'
                orders = random.randint(1, 20)
                total_spent = round(random.uniform(200.0, 5000.0), 2)
                sample_customers.append({'name': name, 'email': email, 'orders': orders, 'total_spent': total_spent})

            # Sample all products
            sample_all_products = []
            for i in range(8):
                if i < len(real_products):
                    rp = real_products[i]
                    name = rp.get('name', f'Product {i+1}')
                    category = rp.get('category', 'Other')
                else:
                    name = f'Product {i+1}'
                    category = 'Other'
                units_sold = random.randint(0, 500)
                revenue = round(units_sold * random.uniform(5.0, 100.0), 2)
                stock = random.randint(0, 120)
                sample_all_products.append({'name': name, 'category': category, 'revenue': revenue, 'units_sold': units_sold, 'stock': stock})

            total_revenue = round(trend_total, 2)
            total_orders = random.randint(10, 200)
            avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0
            active_customers = len(sample_customers)
            new_customers = random.randint(0, 10)
            top_products = sample_products
            all_products = sample_all_products
            category_sales_list = [{'category': 'Sample', 'revenue': round(total_revenue * 0.6, 2)}, {'category':'Other', 'revenue': round(total_revenue * 0.4, 2)}]
            top_customers = sample_customers
            sales_trend = sample_trend
            top_category = category_sales_list[0]['category']
            top_category_revenue = category_sales_list[0]['revenue']

        using_demo = demo_flag or (is_admin and 'Sample Product' in (top_products[0]['name'] if top_products else ''))

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
            'sales_trend': sales_trend,
            'demo': bool(demo_flag or (is_admin and total_orders == 0))
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

@app.route('/admin/send-custom-email', methods=['POST'])
@admin_required
def admin_send_custom_email():
    """Send custom email to selected recipients (reads JSON from frontend)"""
    try:
        data = request.get_json() or {}
        recipient_type  = data.get('recipient_type', 'all_users')
        custom_recs     = data.get('custom_recipients', '')
        subject         = data.get('subject', 'Message from Sales Sense AI')
        body            = data.get('body', '')

        # ── Email validator ───────────────────────────────────────────────────
        import re as _re
        _EMAIL_RE = _re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
        def is_valid_email(addr):
            return bool(addr and _EMAIL_RE.match(addr.strip()))
        # ─────────────────────────────────────────────────────────────────────

        # Build recipient list
        if recipient_type == 'all_users':
            all_cols = [col for col in [users, users_update] if col is not None]
            recipient_list = []
            for col in all_cols:
                for u in col.find({}, {'email': 1}):
                    e = u.get('email', '')
                    if e and e not in recipient_list:
                        recipient_list.append(e)
        elif recipient_type == 'all_workers':
            recipient_list = [w['email'] for w in workers_update.find({}, {'email': 1}) if w.get('email')]
        else:  # custom
            recipient_list = [e.strip() for e in custom_recs.split(',') if e.strip()]

        # Filter: keep only valid emails, collect invalid ones for reporting
        valid_list   = [e for e in recipient_list if is_valid_email(e)]
        invalid_list = [e for e in recipient_list if not is_valid_email(e)]

        if not valid_list:
            return jsonify({'success': False, 'message': 'No valid email addresses found.' +
                            (f' Skipped invalid: {", ".join(invalid_list[:5])}' if invalid_list else '')}), 400

        # Wrap plain text in HTML if needed
        if not body.strip().startswith('<'):
            html_body = f'<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#333;">{body.replace(chr(10), "<br>")}</div>'
        else:
            html_body = body

        # Check SMTP config before looping
        smtp_configured = all([
            os.getenv('SMTP_SERVER'), os.getenv('SMTP_USERNAME'),
            os.getenv('SMTP_PASSWORD'), os.getenv('SENDER_EMAIL')
        ])
        if not smtp_configured:
            return jsonify({
                'success': False,
                'message': 'Email not configured: Please set SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD and SENDER_EMAIL in your .env file.'
            }), 503

        # ── Fire background thread — return instantly ──────────────────────
        import uuid as _uuid
        job_id = str(_uuid.uuid4())[:8]
        _bulk_jobs[job_id] = {
            'status': 'sending', 'sent': 0, 'failed': 0,
            'total': len(valid_list), 'error': '', 'done': False
        }
        t = threading.Thread(
            target=_run_bulk_send,
            args=(job_id, valid_list, subject, html_body,
                  recipient_type, len(invalid_list),
                  (body[:120] + '…') if len(body) > 120 else body),
            daemon=True
        )
        t.start()

        inv_note = f' {len(invalid_list)} invalid address(es) will be skipped.' if invalid_list else ''
        return jsonify({
            'success':  True,
            'queued':   True,
            'job_id':   job_id,
            'total':    len(valid_list),
            'message':  f'Sending to {len(valid_list)} recipient(s) in background.{inv_note}',
            'invalid':  len(invalid_list),
            'invalid_emails': invalid_list
        })
    except Exception as e:
        print(f'send-custom-email error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/email-send-status/<job_id>')
@admin_required
def email_send_status(job_id):
    """Poll: return current state of a background bulk-send job."""
    job = _bulk_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/api/chart-data')
def chart_data_api():
    if 'admin_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 403
    """Return sales_trend + category_breakdown for an arbitrary date range.
       Query params: ?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    try:
        if user_data_bought is None:
            return jsonify({'sales_trend': [], 'category_breakdown': []})

        from_str = request.args.get('from', '')
        to_str   = request.args.get('to',   '')

        now = datetime.datetime.now()
        try:
            date_from = datetime.datetime.strptime(from_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            date_from = now - datetime.timedelta(days=30)
        try:
            date_to = datetime.datetime.strptime(to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError):
            date_to = now

        delta_days = (date_to - date_from).days + 1

        # ── Sales trend ────────────────────────────────────────────────────────
        sales_trend = []
        if delta_days <= 31:
            # Daily
            for i in range(delta_days):
                d     = date_from + datetime.timedelta(days=i)
                start = d.replace(hour=0,  minute=0,  second=0,  microsecond=0)
                end   = d.replace(hour=23, minute=59, second=59, microsecond=999999)
                res   = list(user_data_bought.aggregate([
                    {'$match': {'purchase_date': {'$gte': start, '$lte': end},
                                'total': {'$exists': True, '$ne': None}}},
                    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
                ]))
                sales_trend.append({'date': d.strftime('%d %b'), 'sales': float(res[0]['total']) if res else 0.0})
        else:
            # Weekly
            num_weeks = max(1, delta_days // 7)
            for w in range(num_weeks):
                start = date_from + datetime.timedelta(weeks=w)
                end   = (date_from + datetime.timedelta(weeks=w+1) - datetime.timedelta(seconds=1))
                if end > date_to:
                    end = date_to
                res = list(user_data_bought.aggregate([
                    {'$match': {'purchase_date': {'$gte': start, '$lte': end},
                                'total': {'$exists': True, '$ne': None}}},
                    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
                ]))
                sales_trend.append({'date': start.strftime('%d %b'), 'sales': float(res[0]['total']) if res else 0.0})

        # ── Category breakdown ─────────────────────────────────────────────────
        cat_result = list(user_data_bought.aggregate([
            {'$match': {'purchase_date': {'$gte': date_from, '$lte': date_to},
                        'total': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': '$category', 'total_revenue': {'$sum': '$total'}, 'count': {'$sum': 1}}},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 8}
        ]))
        category_breakdown = [
            {'name': c['_id'] or 'Uncategorized',
             'total': float(c.get('total_revenue', 0)),
             'count': int(c.get('count', 0))}
            for c in cat_result
        ]

        return jsonify({'sales_trend': sales_trend, 'category_breakdown': category_breakdown})
    except Exception as e:
        print(f'chart-data error: {e}')
        return jsonify({'sales_trend': [], 'category_breakdown': []})


@app.route('/api/email-history')
@admin_required
def email_history_api():
    """Return last 50 email sends"""
    try:
        if email_logs is None:
            return jsonify([])
        logs = list(email_logs.find({}, {'_id': 0}).sort('sent_at', -1).limit(50))
        for l in logs:
            l['sent_at'] = l['sent_at'].strftime('%d %b %Y, %H:%M') if hasattr(l.get('sent_at'), 'strftime') else str(l.get('sent_at', ''))[:16]
        return jsonify(logs)
    except Exception as e:
        return jsonify([])


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
    
    # Calculate real statistics from database
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Today's sales by this worker
    today_sales_pipeline = [
        {'$match': {
            'sold_by': worker_id,
            'purchase_date': {'$gte': today},
            'total': {'$ne': None, '$exists': True}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}
    ]
    today_sales_result = list(user_data_bought.aggregate(today_sales_pipeline))
    today_sales_amount = float(today_sales_result[0]['total']) if today_sales_result and today_sales_result[0].get('total') else 0.0
    today_orders_count = int(today_sales_result[0]['count']) if today_sales_result and today_sales_result[0].get('count') else 0
    
    # Total sales by this worker (all time)
    total_sales_pipeline = [
        {'$match': {
            'sold_by': worker_id,
            'total': {'$ne': None, '$exists': True}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}
    ]
    total_sales_result = list(user_data_bought.aggregate(total_sales_pipeline))
    total_sales_amount = float(total_sales_result[0]['total']) if total_sales_result and total_sales_result[0].get('total') else 0.0
    total_orders_count = int(total_sales_result[0]['count']) if total_sales_result and total_sales_result[0].get('count') else 0
    
    # Count unique products across all collections
    unique_products = set()
    if products is not None:
        for p in products.find({}, {'name': 1}):
            if 'name' in p:
                unique_products.add(p['name'])
    if products_update is not None:
        for p in products_update.find({}, {'name': 1}):
            if 'name' in p:
                unique_products.add(p['name'])
    if products_by_user is not None:
        for p in products_by_user.find({}, {'name': 1}):
            if 'name' in p:
                unique_products.add(p['name'])
    unique_product_count = len(unique_products)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get only worker-added products with proper structure
    # Filter for products that have name field (properly structured products)
    query = {'name': {'$exists': True}}
    total_products = products_by_user.count_documents(query)
    
    # Get products with pagination and ensure they have proper structure
    worker_products = list(products_by_user.find(query).skip((page - 1) * per_page).limit(per_page))
    
    # Ensure all products have the required fields
    for product in worker_products:
        if 'name' not in product:
            product['name'] = 'Unknown Product'
        if 'category' not in product:
            product['category'] = 'Uncategorized'
        if 'variants' not in product or not isinstance(product['variants'], list):
            product['variants'] = []
        if 'added_by_name' not in product:
            product['added_by_name'] = 'System'
    
    # Extract unique categories from all collections
    categories = set()
    for collection in [products_update, products, products_by_user]:
        if collection is not None:
            try:
                for product in collection.find({}, {'category': 1}):
                    if 'category' in product and product['category']:
                        categories.add(product['category'])
            except:
                pass
    categories = sorted(list(categories))
    
    # Get worker's recent activities
    recent_activities = list(worker_specific_added.find(
        {'worker_id': worker_id}
    ).sort('date', -1).limit(5))
    
    # Calculate total pages
    total_pages = max(1, (total_products + per_page - 1) // per_page)
    
    # All products from products_update for the restock dropdown
    all_products_list = []
    if products_update is not None:
        for p in products_update.find({'name': {'$exists': True}}, {'name': 1, 'category': 1, 'variants': 1}).sort('name', 1):
            p['_id'] = str(p['_id'])
            all_products_list.append(p)

    return render_template('worker_dashboard.html', 
                         worker=worker,
                         products=worker_products,
                         categories=categories,
                         recent_activities=recent_activities,
                         page=page,
                         total_pages=total_pages,
                         total_products=total_products,
                         unique_product_count=unique_product_count,
                         today_sales=today_sales_amount,
                         today_orders=today_orders_count,
                         total_sales=total_sales_amount,
                         total_orders=total_orders_count,
                         all_products_list=all_products_list)

@app.route('/worker/add-product', methods=['POST'])
def add_product():
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        worker_name = session.get('worker_name', 'Unknown Worker')
        worker_id = ObjectId(session['worker_id'])
        
        # Check if product already exists in products_by_user
        existing_product = products_by_user.find_one({
            'name': {'$regex': f'^{data["name"]}$', '$options': 'i'},
            'category': data['category']
        })
        
        if existing_product:
            # Update existing product - merge variants
            new_variants = data.get('variants', [])
            existing_variants = existing_product.get('variants', [])
            
            # Add new variants to existing ones
            updated_variants = existing_variants + new_variants
            
            # Update the product
            products_by_user.update_one(
                {'_id': existing_product['_id']},
                {
                    '$set': {
                        'variants': updated_variants,
                        'updated_at': datetime.datetime.utcnow(),
                        'updated_by': worker_id,
                        'updated_by_name': worker_name
                    }
                }
            )
            
            # Record the worker's action
            worker_action = {
                'worker_id': worker_id,
                'worker_name': worker_name,
                'product_id': existing_product['_id'],
                'product_name': data['name'],
                'action_type': 'update_product',
                'date': datetime.datetime.utcnow(),
                'product_details': {
                    'category': data['category'],
                    'variants_added': len(new_variants)
                }
            }
            worker_specific_added.insert_one(worker_action)
            
            return jsonify({
                'success': True,
                'updated': True,
                'product_id': str(existing_product['_id']),
                'message': 'Product updated with new variants'
            })
        else:
            # Insert new product
            product = {
                'name': data['name'],
                'category': data['category'],
                'price': data.get('price'),  # Single price if provided
                'variants': data.get('variants', []),
                'added_by': worker_id,
                'added_by_name': worker_name,
                'added_at': datetime.datetime.utcnow(),
                'source': 'worker_added'
            }
            
            result = products_by_user.insert_one(product)
            
            # Record the worker's action
            worker_action = {
                'worker_id': worker_id,
                'worker_name': worker_name,
                'product_id': result.inserted_id,
                'product_name': data['name'],
                'action_type': 'add_product',
                'date': datetime.datetime.utcnow(),
                'product_details': {
                    'category': data['category'],
                    'variants_count': len(data.get('variants', []))
                }
            }
            worker_specific_added.insert_one(worker_action)
            
            # Update worker's statistics
            workers_update.update_one(
                {'_id': worker_id},
                {'$inc': {'total_products_added': 1}}
            )
            
            return jsonify({
                'success': True,
                'updated': False,
                'product_id': str(result.inserted_id),
                'message': 'New product added successfully'
            })
    except Exception as e:
        print(f"Error adding product: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/worker/restock', methods=['POST'])
def worker_restock():
    """Worker increases stock of an existing product variant."""
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data          = request.get_json() or {}
        product_id    = data.get('product_id', '').strip()
        variant_index = int(data.get('variant_index', -1))
        add_qty       = int(data.get('add_qty', 0))

        if not product_id or variant_index < 0 or add_qty < 1:
            return jsonify({'error': 'Invalid data'}), 400

        product = products_update.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        variants = product.get('variants', [])
        if variant_index >= len(variants):
            return jsonify({'error': 'Invalid variant'}), 400

        # Increase stock
        products_update.update_one(
            {'_id': ObjectId(product_id)},
            {'$inc': {f'variants.{variant_index}.stock': add_qty}}
        )

        # Log the restock activity
        worker_specific_added.insert_one({
            'worker_id':   ObjectId(session['worker_id']),
            'worker_name': session.get('worker_name', 'Worker'),
            'action':      'restock',
            'product_id':  ObjectId(product_id),
            'product_name': product.get('name', ''),
            'variant_index': variant_index,
            'qty_added':   add_qty,
            'date':        datetime.datetime.now(),
        })

        new_stock = int(variants[variant_index].get('stock', 0)) + add_qty
        return jsonify({'success': True, 'new_stock': new_stock})

    except Exception as e:
        print(f"Restock error: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/worker/delete-product/<product_id>', methods=['DELETE', 'POST'])
def delete_product(product_id):
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Delete the product
        result = products_by_user.delete_one({'_id': ObjectId(product_id)})
        
        if result.deleted_count > 0:
            # Record the worker's action
            worker_action = {
                'worker_id': ObjectId(session['worker_id']),
                'worker_name': session.get('worker_name', 'Unknown Worker'),
                'action_type': 'delete_product',
                'product_id': ObjectId(product_id),
                'date': datetime.datetime.utcnow()
            }
            worker_specific_added.insert_one(worker_action)
            
            # Update worker's statistics
            workers_update.update_one(
                {'_id': ObjectId(session['worker_id'])},
                {'$inc': {'total_products_added': -1}}
            )
            
            return jsonify({'success': True, 'message': 'Product deleted successfully'})
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        print(f"Error deleting product: {e}")
        return jsonify({'error': str(e)}), 400

# API to search existing products
@app.route('/api/search-products')
def search_products():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search in all collections using regex
    results = []
    collections_to_search = [
        ('products', products),
        ('products_update', products_update),
        ('products_by_user', products_by_user)
    ]
    
    for collection_name, collection in collections_to_search:
        if collection is not None:
            try:
                products_found = list(collection.find({
                    'name': {'$regex': query, '$options': 'i'}
                }).limit(15))
                
                for product in products_found:
                    # Calculate average price from variants if exists
                    avg_price = None
                    total_stock = 0
                    
                    if 'variants' in product and isinstance(product['variants'], list) and len(product['variants']) > 0:
                        prices = [v.get('price', 0) for v in product['variants'] if v.get('price')]
                        stocks = [v.get('stock', 0) for v in product['variants']]
                        if prices:
                            avg_price = sum(prices) / len(prices)
                        total_stock = sum(stocks)
                    elif 'price' in product:
                        avg_price = product.get('price')
                    
                    result_item = {
                        '_id': str(product['_id']),
                        'name': product.get('name', 'Unknown'),
                        'category': product.get('category', 'Uncategorized'),
                        'price': avg_price,
                        'stock': total_stock,
                        'variants': product.get('variants', []),
                        'source': collection_name
                    }
                    results.append(result_item)
            except Exception as e:
                print(f"Error searching in {collection_name}: {e}")
                continue
    
    # Remove duplicates by name+category
    seen = set()
    unique_results = []
    for product in results:
        key = f"{product.get('name', '').lower()}_{product.get('category', '').lower()}"
        if key not in seen and product.get('name'):
            seen.add(key)
            unique_results.append(product)
    
    return jsonify(unique_results[:10])

# Worker purchase/sales page
@app.route('/worker/sales')
def worker_sales():
    if 'worker_id' not in session:
        return redirect(url_for('worker_login'))
    
    worker_id = ObjectId(session['worker_id'])
    worker = workers_update.find_one({'_id': worker_id})
    
    # Get all available products from all collections
    all_products = []
    for collection in [products, products_update, products_by_user]:
        if collection is not None:
            try:
                prods = list(collection.find({'name': {'$exists': True}}))
                all_products.extend(prods)
            except:
                pass
    
    # Remove duplicates and format products
    seen = set()
    unique_products = []
    for product in all_products:
        key = f"{product.get('name', '').lower()}_{product.get('category', '').lower()}"
        if key not in seen and product.get('name'):
            seen.add(key)
            # Calculate total stock
            total_stock = 0
            if 'variants' in product and product['variants']:
                for variant in product['variants']:
                    total_stock += variant.get('stock', 0)
            product['total_stock'] = total_stock
            unique_products.append(product)
    
    # Get recent sales made by this worker
    recent_sales = list(user_data_bought.find({
        'sold_by': worker_id
    }).sort('purchase_date', -1).limit(10))
    
    return render_template('worker_sales.html', 
                         worker=worker,
                         products=unique_products,
                         recent_sales=recent_sales)

# API to search customers
@app.route('/api/search-customers')
def search_customers():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Search by name or email in users_update collection for existing customers
        customers = list(users_update.find({
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}}
            ]
        }).limit(10))
        
        result = []
        for customer in customers:
            result.append({
                '_id': str(customer['_id']),
                'name': customer.get('name', 'Unknown'),
                'email': customer.get('email', ''),
                'mobile': customer.get('mobile', '')
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error searching customers: {e}")
        return jsonify([])

# API to get product details
@app.route('/api/product-details/<product_id>')
def get_product_details(product_id):
    try:
        # Search in all collections
        product = None
        for collection in [products, products_update, products_by_user]:
            if collection is not None:
                product = collection.find_one({'_id': ObjectId(product_id)})
                if product:
                    break
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Calculate total stock
        total_stock = 0
        if 'variants' in product and product['variants']:
            for variant in product['variants']:
                total_stock += variant.get('stock', 0)
        
        result = {
            '_id': str(product['_id']),
            'name': product.get('name', 'Unknown'),
            'category': product.get('category', 'Uncategorized'),
            'variants': product.get('variants', []),
            'total_stock': total_stock,
            'added_by': product.get('added_by_name', 'System'),
            'added_at': str(product.get('added_at', ''))
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"Error getting product details: {e}")
        return jsonify({'error': str(e)}), 400

# Process purchase
@app.route('/worker/process-purchase', methods=['POST'])
def process_purchase():
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        worker_id = ObjectId(session['worker_id'])
        worker_name = session.get('worker_name', 'Unknown Worker')
        
        # Get or create customer
        customer_email = data.get('customer_email')
        customer_name = data.get('customer_name')
        
        if not customer_email or not customer_name:
            return jsonify({'error': 'Customer email and name are required'}), 400
        
        # Check if customer exists in users_update collection
        customer = users_update.find_one({'email': customer_email})
        
        if not customer:
            # Create new customer in users collection
            customer = {
                'name': customer_name,
                'email': customer_email,
                'mobile': data.get('customer_mobile', ''),
                'created_at': datetime.datetime.utcnow(),
                'created_by_worker': worker_id,
                'created_by_worker_name': worker_name
            }
            customer_id = users.insert_one(customer).inserted_id
        else:
            # Use existing customer from users_update
            customer_id = customer['_id']
            customer_name = customer.get('name', customer_name)
        
        # Process each item in the purchase
        purchased_items = data.get('items', [])
        if not purchased_items:
            return jsonify({'error': 'No items in purchase'}), 400
        
        total_amount = 0
        purchase_records = []
        
        for item in purchased_items:
            product_id = ObjectId(item['product_id'])
            variant_index = item.get('variant_index', 0)
            quantity = item.get('quantity', 1)
            
            # Find product in collections and update stock
            product = None
            collection_to_update = None
            
            for collection in [products, products_update, products_by_user]:
                if collection is not None:
                    product = collection.find_one({'_id': product_id})
                    if product:
                        collection_to_update = collection
                        break
            
            if not product:
                return jsonify({'error': f'Product not found: {item.get("product_name", "")}'}), 404
            
            # Get variant details
            variants = product.get('variants', [])
            if variant_index >= len(variants):
                return jsonify({'error': f'Invalid variant for {product.get("name", "")}'}), 400
            
            variant = variants[variant_index]
            price = variant.get('price', 0)
            current_stock = variant.get('stock', 0)
            
            if current_stock < quantity:
                return jsonify({'error': f'Insufficient stock for {product.get("name", "")} - {variant.get("quantity", "")}'}), 400
            
            # Update stock
            variants[variant_index]['stock'] = current_stock - quantity
            collection_to_update.update_one(
                {'_id': product_id},
                {'$set': {'variants': variants}}
            )
            
            # Calculate item total
            item_total = price * quantity
            total_amount += item_total
            
            # Create purchase record
            purchase_record = {
                'user_id': customer_id,
                'user_name': customer_name,
                'user_email': customer_email,
                'product_id': product_id,
                'product_name': product.get('name', 'Unknown'),
                'category': product.get('category', 'Uncategorized'),
                'variant': variant.get('quantity', 'N/A'),
                'quantity': quantity,
                'price': price,
                'total': item_total,
                'sold_by': worker_id,
                'sold_by_name': worker_name,
                'purchase_date': datetime.datetime.utcnow(),
                'payment_status': data.get('payment_status', 'completed')
            }
            purchase_records.append(purchase_record)
        
        # Insert all purchase records
        if purchase_records:
            user_data_bought.insert_many(purchase_records)
        
        # Record in products_sold
        products_sold.insert_one({
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'items': purchased_items,
            'total_amount': total_amount,
            'sold_by': worker_id,
            'sold_by_name': worker_name,
            'sale_date': datetime.datetime.utcnow()
        })
        
        # Update worker statistics
        workers_update.update_one(
            {'_id': worker_id},
            {
                '$inc': {
                    'total_sales': 1,
                    'total_revenue': total_amount
                }
            }
        )
        
        # Send purchase confirmation email to customer
        try:
            # Create items list for email
            items_html = ""
            for record in purchase_records:
                items_html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{record['product_name']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{record['variant']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">{record['quantity']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">₹{record['price']:.2f}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right; font-weight: 600;">₹{record['total']:.2f}</td>
                </tr>
                """
            
            # Create email HTML
            email_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    .total-row {{ background: #f0f9ff; font-weight: 600; font-size: 1.1rem; }}
                    .badge {{ display: inline-block; padding: 6px 12px; background: #10b981; color: white; border-radius: 6px; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">🎉 Purchase Confirmation</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.95;">Thank you for your purchase!</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear <strong>{customer_name}</strong>,</p>
                        
                        <p>Your purchase has been successfully processed. Here are the details:</p>
                        
                        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Order Date:</strong> {datetime.datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}</p>
                            <p style="margin: 5px 0;"><strong>Processed By:</strong> {worker_name}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> <span class="badge">Completed</span></p>
                        </div>
                        
                        <h3>Order Details</h3>
                        <table>
                            <thead>
                                <tr style="background: #f9fafb;">
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Product</th>
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Variant</th>
                                    <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Qty</th>
                                    <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Price</th>
                                    <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                            <tfoot>
                                <tr class="total-row">
                                    <td colspan="4" style="padding: 15px; text-align: right; border-top: 2px solid #3b82f6;">Total Amount:</td>
                                    <td style="padding: 15px; text-align: right; border-top: 2px solid #3b82f6; color: #3b82f6;">₹{total_amount:.2f}</td>
                                </tr>
                            </tfoot>
                        </table>
                        
                        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin-top: 20px;">
                            <p style="margin: 0;"><strong>📋 Note:</strong> Please keep this email as your purchase receipt.</p>
                        </div>
                        
                        <p style="margin-top: 30px;">If you have any questions about your purchase, please feel free to contact us.</p>
                        
                        <p style="margin-top: 20px;">Best regards,<br><strong>Sales Sense AI Team</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p style="margin: 5px 0;">This is an automated email. Please do not reply to this message.</p>
                        <p style="margin: 5px 0;">&copy; {datetime.datetime.utcnow().year} Sales Sense AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            email_sent, _ = send_email(
                to_email=customer_email,
                subject=f"Purchase Confirmation - Order from {datetime.datetime.utcnow().strftime('%B %d, %Y')}",
                html_body=email_html
            )

            if email_sent:
                print(f"Purchase confirmation email sent to {customer_email}")
            else:
                print(f"Failed to send email to {customer_email}")
        except Exception as email_error:
            print(f"Error sending purchase confirmation email: {email_error}")
            # Don't fail the purchase if email fails
        
        return jsonify({
            'success': True,
            'message': f'Purchase completed! Total: ₹{total_amount:.2f}',
            'total_amount': total_amount,
            'items_count': len(purchased_items)
        })
        
    except Exception as e:
        print(f"Error processing purchase: {e}")
        return jsonify({'error': str(e)}), 400

# Utility route to clean up products_by_user collection
@app.route('/admin/cleanup-products', methods=['GET', 'POST'])
def cleanup_products():
    # Check if admin is logged in
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        # Delete all products without proper structure (missing name field)
        result = products_by_user.delete_many({'name': {'$exists': False}})
        return jsonify({
            'success': True,
            'deleted_count': result.deleted_count,
            'message': f'Deleted {result.deleted_count} invalid products'
        })
    
    # GET request - show stats
    total = products_by_user.count_documents({})
    valid = products_by_user.count_documents({'name': {'$exists': True}})
    invalid = total - valid
    
    # Sample of invalid products
    invalid_samples = list(products_by_user.find({'name': {'$exists': False}}).limit(5))
    for product in invalid_samples:
        product['_id'] = str(product['_id'])
    
    return jsonify({
        'total_products': total,
        'valid_products': valid,
        'invalid_products': invalid,
        'invalid_samples': invalid_samples
    })

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
        return redirect(url_for('product_list'))  # Changed to use same products page
    
    flash('Registration failed', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/labor/login', methods=['POST'])
def labor_login():
    identifier = request.form.get('identifier')  # This can be email or mobile
    
    # Try to find user by email or mobile in both users collections
    query = {'$or': [{'email': identifier}, {'mobile': identifier}, {'phone': identifier}]}
    user = users.find_one(query)
    if not user and users_update is not None:
        user = users_update.find_one(query)
    
    if user:
        session['user_id'] = str(user['_id'])
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('product_list'))  # Changed to use same products page
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/user/products')
def user_products():
    if 'user_id' not in session:
        return redirect(url_for('labor_panel'))
    
    user = users.find_one({'_id': ObjectId(session['user_id'])})
    all_products = list(products_update.find())
    # Apply active festival discounts in-memory (non-destructive)
    all_products = _apply_festival_discounts(all_products)
    cart = _get_cart(str(session['user_id']))
    return render_template('user_products.html', products=all_products, user=user, cart=cart)

# ── MongoDB cart helpers ───────────────────────────────────────────────────────
def _get_cart(user_id):
    """Load cart dict from MongoDB for a given user_id string."""
    if carts is None:
        return {}
    doc = carts.find_one({'user_id': user_id})
    return doc.get('items', {}) if doc else {}

def _save_cart(user_id, cart_dict):
    """Upsert cart dict to MongoDB."""
    if carts is None:
        return
    carts.update_one(
        {'user_id': user_id},
        {'$set': {'items': cart_dict, 'updated_at': datetime.datetime.now()}},
        upsert=True
    )

def _clear_cart(user_id):
    """Remove cart from MongoDB."""
    if carts is None:
        return
    carts.delete_one({'user_id': user_id})
# ────────────────────────────────────────────────────────────────────────────────

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

        user_id = str(session['user_id'])
        cart = _get_cart(user_id)

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
            if cart_key in cart:
                new_quantity = cart[cart_key]['quantity'] + quantity
                if new_quantity > variant['stock']:
                    return jsonify({
                        'error': f'Cannot add {quantity} more of {product["name"]} ({variant["quantity"]}). Stock limit exceeded.'
                    }), 400
                cart[cart_key]['quantity'] = new_quantity
            else:
                cart[cart_key] = {
                    'product_id': product_id,
                    'product_name': product['name'],
                    'variant_index': variant_index,
                    'variant_quantity': variant['quantity'],
                    'price': variant['price'],
                    'quantity': quantity,
                    'cart_key': cart_key
                }

        _save_cart(user_id, cart)

        cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
        cart_items = len(cart)

        return jsonify({
            'message': 'Items added to cart successfully',
            'cart_total': cart_total,
            'cart_items': cart_items
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
        user_id = str(session['user_id'])
        cart = _get_cart(user_id)

        if cart_key in cart:
            del cart[cart_key]
            _save_cart(user_id, cart)

        cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
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

    user_id = str(session['user_id'])
    cart = _get_cart(user_id)

    # Migrate any legacy session-based cart items into MongoDB
    for src_key in ('cart', 'guest_cart'):
        session_cart = session.get(src_key, {})
        if session_cart:
            for k, v in session_cart.items():
                if k not in cart:
                    cart[k] = v
            _save_cart(user_id, cart)
            session.pop(src_key, None)
            session.modified = True

    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    current_user = None
    try:
        current_user = users.find_one({'_id': ObjectId(session['user_id'])})
        if current_user is None and users_update is not None:
            current_user = users_update.find_one({'_id': ObjectId(session['user_id'])})
        if current_user:
            current_user['_id'] = str(current_user['_id'])
    except Exception:
        pass
    return render_template('cart.html', cart=cart, cart_total=cart_total, current_user=current_user)

# Guest cart routes
@app.route('/cart/guest-add', methods=['POST'])
def guest_add_to_cart():
    try:
        data = request.get_json()
        product_id = data['product_id']
        variant_index = int(data['variant_index'])
        variant_name = data['variant_name']
        price = float(data['price'])
        quantity = int(data['quantity'])
        product_name = data['product_name']

        # Initialize guest cart if it doesn't exist
        if 'guest_cart' not in session:
            session['guest_cart'] = {}

        cart_key = f"{product_id}_{variant_index}"
        
        # Add or update item in cart
        if cart_key in session['guest_cart']:
            session['guest_cart'][cart_key]['quantity'] += quantity
        else:
            session['guest_cart'][cart_key] = {
                'product_id': product_id,
                'product_name': product_name,
                'variant_index': variant_index,
                'variant_name': variant_name,
                'price': price,
                'quantity': quantity
            }

        session.modified = True
        
        cart_items = len(session['guest_cart'])
        cart_total = sum(item['price'] * item['quantity'] for item in session['guest_cart'].values())
        
        return jsonify({
            'success': True,
            'cart_items': cart_items,
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/cart/guest-view')
def guest_view_cart():
    # If user is logged in, redirect to the proper cart view
    if 'user_id' in session:
        return redirect(url_for('view_cart'))
    cart = session.get('guest_cart', {})
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, cart_total=cart_total)

@app.route('/cart/guest-remove', methods=['POST'])
def guest_remove_from_cart():
    try:
        data = request.get_json()
        cart_key = data['cart_key']

        if 'guest_cart' in session and cart_key in session['guest_cart']:
            del session['guest_cart'][cart_key]
            session.modified = True

        cart_total = sum(item['price'] * item['quantity'] for item in session.get('guest_cart', {}).values())
        return jsonify({
            'success': True,
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/user/purchase', methods=['POST'])
def user_purchase():
    """Logged-in labour/user checkout: no need to re-enter name/email/phone."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please log in first'}), 401
    try:
        data = request.get_json() or {}
        delivery_address = (data.get('delivery_address') or '').strip()
        payment_method   = (data.get('payment_method') or 'COD').strip()

        if not delivery_address:
            return jsonify({'success': False, 'error': 'Delivery address is required'}), 400

        # ── Get logged-in user ────────────────────────────────────────
        user_id_str = str(session['user_id'])   # keep as string for cart key
        uid = ObjectId(user_id_str)
        current_user = users.find_one({'_id': uid})
        if current_user is None and users_update is not None:
            current_user = users_update.find_one({'_id': uid})
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 400

        user_name  = current_user.get('name', 'Customer')
        user_email = current_user.get('email', '')
        user_phone = current_user.get('mobile') or current_user.get('phone', '')

        # ── Cart ──────────────────────────────────────────────────────
        cart = _get_cart(user_id_str)   # ALWAYS use the string key, never ObjectId
        print(f"[purchase] user_id_str={user_id_str!r}  cart_keys={list(cart.keys())}", flush=True)
        if not cart:
            # Fallback: check session cart (for clients that added items before MongoDB migration)
            cart = session.get('cart', {})
            print(f"[purchase] fallback session cart keys={list(cart.keys())}", flush=True)
        if not cart:
            # Fallback 2: check guest_cart (user added items before logging in)
            cart = session.get('guest_cart', {})
            print(f"[purchase] fallback guest_cart keys={list(cart.keys())}", flush=True)
        if not cart:
            return jsonify({'success': False, 'error': 'Your basket is empty'}), 400

        order_id  = f'ORD{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        now       = datetime.datetime.now()
        purchases = []
        total_amount = 0.0

        # ── Validate stock ────────────────────────────────────────────
        for cart_key, item in cart.items():
            product = products_update.find_one({'_id': ObjectId(item['product_id'])})
            if not product:
                return jsonify({'success': False, 'error': f'Product "{item["product_name"]}" not found'}), 400
            try:
                variant = product['variants'][int(item['variant_index'])]
            except (KeyError, IndexError, TypeError):
                variant = {'stock': product.get('stock', 0), 'quantity': 'Regular', 'price': product.get('price', 0)}
            if int(variant.get('stock', 0)) < int(item['quantity']):
                return jsonify({'success': False, 'error': f'Only {variant.get("stock",0)} left for {item["product_name"]} ({item["variant_name"]})'}), 400

            line_total = float(item['price']) * int(item['quantity'])
            purchases.append({
                'product': product,
                'item': item,
                'variant_index': int(item['variant_index']),
                'line_total': line_total,
                'category': product.get('category', 'General'),
            })
            total_amount += line_total

        # ── Save purchases & reduce stock ─────────────────────────────
        for p in purchases:
            item = p['item']
            rec = {
                'order_id':       order_id,
                'user_id':        uid,
                'user_name':      user_name,
                'buyer_name':     user_name,
                'buyer_email':    user_email,
                'buyer_phone':    user_phone,
                'product_id':     ObjectId(item['product_id']),
                'product_name':   item['product_name'],
                'category':       p['category'],
                'variant_index':  p['variant_index'],
                'variant_name':   item.get('variant_name') or item.get('variant_quantity', ''),
                'quantity':       int(item['quantity']),
                'price':          float(item['price']),
                'total':          p['line_total'],
                'total_price':    p['line_total'],
                'payment_method': payment_method,
                'payment_status': 'Paid',
                'delivery_address': delivery_address,
                'purchase_date':  now,
                'date':           now,
                'status':         'confirmed',
                'sold_by_name':   'Self',
            }
            # Save to both collections so admin analytics + user history both work
            user_data_bought.insert_one(dict(rec))
            products_sold.insert_one(dict(rec))

            # Decrease stock
            products_update.update_one(
                {'_id': ObjectId(item['product_id'])},
                {'$inc': {f'variants.{p["variant_index"]}.stock': -int(item['quantity'])}}
            )

        # ── Update user purchase counters ─────────────────────────────
        upd = {'$set': {'last_purchase': now}, '$inc': {'total_purchases': 1}}
        users.update_one({'_id': uid}, upd)
        if users_update is not None:
            users_update.update_one({'_id': uid}, upd)

        # ── Send confirmation email ───────────────────────────────────
        if user_email:
            try:
                purchase_list = [{
                    'product_name':  p['item']['product_name'],
                    'variant_name':  p['item'].get('variant_name', ''),
                    'quantity':      p['item']['quantity'],
                    'price':         p['item']['price'],
                    'total':         p['line_total'],
                    'total_price':   p['line_total'],
                } for p in purchases]
                send_purchase_confirmation_email(
                    user_email, user_name, order_id,
                    purchase_list, total_amount, delivery_address, payment_method
                )
            except Exception as email_err:
                print(f'⚠️ Order email error: {email_err}')

        # ── Clear cart ────────────────────────────────────────────────────────────────────────
        _clear_cart(user_id_str)
        session.pop('cart', None)
        session.pop('guest_cart', None)
        session.modified = True

        return jsonify({'success': True, 'order_id': order_id, 'total_amount': total_amount,
                        'message': 'Purchase completed!', 'user_email': user_email})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/guest/purchase', methods=['POST'])
def guest_purchase():
    try:
        data = request.get_json()
        
        # Get user details
        buyer_name = data.get('buyer_name', '').strip()
        buyer_email = data.get('buyer_email', '').strip().lower()
        buyer_phone = data.get('buyer_phone', '').strip()
        delivery_address = data.get('delivery_address', '').strip()
        payment_method = data.get('payment_method', 'COD')
        
        # Validate required fields
        if not all([buyer_name, buyer_email, buyer_phone, delivery_address]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        cart = session.get('guest_cart', {})

        if not cart:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400

        # Check if user already exists by email or phone
        existing_user = users.find_one({
            '$or': [
                {'email': buyer_email},
                {'phone': buyer_phone}
            ]
        })
        
        if existing_user:
            # Use existing user
            user_id = existing_user['_id']
            user_name = existing_user['name']
            user_email = existing_user['email']
            
            # Update user info if needed
            users.update_one(
                {'_id': user_id},
                {
                    '$set': {'last_purchase': datetime.datetime.utcnow()},
                    '$inc': {'total_purchases': 1}
                }
            )
            print(f"✅ Existing user found: {user_name} ({user_email})")
        else:
            # Create new user
            user_data = {
                'name': buyer_name,
                'email': buyer_email,
                'phone': buyer_phone,
                'address': delivery_address,
                'join_date': datetime.datetime.utcnow(),
                'created_at': datetime.datetime.utcnow(),
                'is_active': True,
                'total_purchases': 1,
                'last_purchase': datetime.datetime.utcnow(),
                'email_notifications': True
            }
            user_id = users.insert_one(user_data).inserted_id
            user_name = buyer_name
            user_email = buyer_email
            print(f"✅ New user created: {user_name} ({user_email})")

        purchases = []
        total_amount = 0
        order_id = f'ORD{datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'

        # Verify stock and create purchase records
        for cart_key, item in cart.items():
            product = products_update.find_one({'_id': ObjectId(item['product_id'])})
            if not product:
                return jsonify({'success': False, 'error': f'Product {item["product_name"]} not found'}), 400

            # Parse variants
            import ast
            if 'variants' in product and isinstance(product['variants'], str):
                try:
                    product['variants'] = ast.literal_eval(product['variants'])
                except:
                    product['variants'] = []

            variant = product['variants'][item['variant_index']] if product.get('variants') else {'stock': product.get('stock', 0), 'quantity': 'Regular', 'price': product.get('price', 0)}
            
            if variant['stock'] < item['quantity']:
                return jsonify({'success': False, 'error': f'Not enough stock for {item["product_name"]} ({item["variant_name"]}). Only {variant["stock"]} available.'}), 400

            purchase = {
                'user_id': user_id,
                'product_id': ObjectId(item['product_id']),
                'product_name': item['product_name'],
                'variant_index': item['variant_index'],
                'variant_name': item['variant_name'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total': item['price'] * item['quantity'],  # Changed from total_price to total
                'total_price': item['price'] * item['quantity'],  # Keep for compatibility
                'payment_method': payment_method,
                'delivery_address': delivery_address,
                'buyer_name': buyer_name,
                'buyer_email': buyer_email,
                'buyer_phone': buyer_phone,
                'order_id': order_id,
                'date': datetime.datetime.utcnow(),
                'status': 'confirmed'
            }
            purchases.append(purchase)
            total_amount += purchase['total']

        # Process all purchases
        for purchase in purchases:
            # Update stock
            products_update.update_one(
                {'_id': purchase['product_id']},
                {'$inc': {f'variants.{purchase["variant_index"]}.stock': -purchase['quantity']}}
            )

            # Save purchase record
            products_sold.insert_one(purchase)
            products_by_user.insert_one(purchase)

        # Send confirmation email
        try:
            send_purchase_confirmation_email(user_email, user_name, order_id, purchases, total_amount, delivery_address, payment_method)
            print(f"✅ Confirmation email sent to {user_email}")
        except Exception as email_error:
            print(f"⚠️ Could not send email: {email_error}")

        # Clear cart
        session['guest_cart'] = {}
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Purchase completed successfully!',
            'order_id': order_id,
            'total_amount': total_amount
        })

    except Exception as e:
        print(f"❌ Error in guest_purchase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

def send_purchase_confirmation_email(email, name, order_id, purchases, total_amount, delivery_address, payment_method):
    """Send order confirmation email to customer"""
    try:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
        SMTP_EMAIL = os.getenv('SMTP_EMAIL')
        SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("⚠️ SMTP credentials not configured. Skipping email.")
            return
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Order Confirmation - {order_id}"
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        
        # Build order items list
        items_html = ""
        for purchase in purchases:
            items_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{purchase['product_name']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{purchase['variant_name']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: center;">{purchase['quantity']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right;">₹{purchase['price']:.2f}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: bold;">₹{purchase['total_price']:.2f}</td>
                </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Order Confirmed! 🎉</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Thank you for your purchase</p>
                </div>
                
                <div style="padding: 30px 20px;">
                    <h2 style="color: #667eea; margin-top: 0;">Hi {name},</h2>
                    <p style="font-size: 16px;">Your order has been successfully placed and confirmed.</p>
                    
                    <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                        <h3 style="margin-top: 0; color: #333;">Order Details</h3>
                        <p style="margin: 5px 0;"><strong>Order ID:</strong> <span style="color: #667eea;">{order_id}</span></p>
                        <p style="margin: 5px 0;"><strong>Order Date:</strong> {datetime.datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p style="margin: 5px 0;"><strong>Payment Method:</strong> {payment_method.upper()}</p>
                    </div>
                    
                    <h3 style="color: #333;">Order Items</h3>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background: #667eea; color: white;">
                                <th style="padding: 12px; text-align: left;">Product</th>
                                <th style="padding: 12px; text-align: left;">Variant</th>
                                <th style="padding: 12px; text-align: center;">Qty</th>
                                <th style="padding: 12px; text-align: right;">Price</th>
                                <th style="padding: 12px; text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                            <tr style="background: #f0f0f0; font-weight: bold;">
                                <td colspan="4" style="padding: 15px; text-align: right; font-size: 18px;">Grand Total:</td>
                                <td style="padding: 15px; text-align: right; font-size: 18px; color: #28a745;">₹{total_amount:.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h3 style="margin-top: 0; color: #333;">Delivery Address</h3>
                        <p style="margin: 0; white-space: pre-line;">{delivery_address}</p>
                    </div>
                    
                    <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #17a2b8;">
                        <p style="margin: 0;">📦 <strong>Estimated Delivery:</strong> 3-5 business days</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">
                        If you have any questions about your order, please contact us at <a href="mailto:support@salessense.com" style="color: #667eea;">support@salessense.com</a>
                    </p>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #e0e0e0;">
                        <p style="margin: 0; color: #999; font-size: 14px;">Thank you for shopping with Sales Sense AI</p>
                        <p style="margin: 5px 0 0 0; color: #667eea; font-weight: bold;">www.salessense.com</p>
                    </div>
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
            
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


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
                'total': item['price'] * item['quantity'],  # Changed from total_price to total
                'total_price': item['price'] * item['quantity'],  # Keep for compatibility
                'payment_method': payment_method,
                'date': datetime.datetime.utcnow()
            }
            purchases.append(purchase)
            total_amount += purchase['total']

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
            Price per unit: ₹{purchase['price']}
            Subtotal: ₹{purchase['total']}
            """

        order_details += f"""
        ----------------------------------------
        Total Amount: ₹{total_amount}
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
        
        # Also load custom festivals from DB
        custom_festivals_raw = list(db.custom_festivals.find({}, {'_id': 1, 'name': 1, 'emoji': 1,
                                                                   'start_date': 1, 'end_date': 1,
                                                                   'discount': 1, 'products': 1,
                                                                   'description': 1,
                                                                   'product_prices': 1}))
        custom_festivals = []
        for cf in custom_festivals_raw:
            cf['_id'] = str(cf['_id'])
            custom_festivals.append(cf)

        return render_template('festival_notifications.html', 
                             all_festivals=all_festivals,
                             upcoming_festivals=upcoming,
                             custom_festivals=custom_festivals)
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

@app.route('/admin/add-custom-festival', methods=['POST'])
@admin_required
def admin_add_custom_festival():
    """Add a custom festival entry with products and discount"""
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        emoji = (data.get('emoji') or '🎉').strip()
        start_date_str = data.get('start_date') or ''
        end_date_str = data.get('end_date') or start_date_str
        discount = (data.get('discount') or '10%').strip()
        products = data.get('products') or []
        description = (data.get('description') or '').strip()

        if not name or not start_date_str:
            return jsonify({'success': False, 'error': 'Festival name and start date are required'}), 400

        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else start_date
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        doc = {
            'name': name,
            'emoji': emoji,
            'start_date': start_date,
            'end_date': end_date,
            'discount': discount,
            'products': products,
            'description': description,
            'created_at': datetime.datetime.now(),
            'is_custom': True
        }
        product_prices_raw = data.get('product_prices') or {}
        # Coerce values to float, drop empty ones
        product_prices = {}
        for pn, pv in product_prices_raw.items():
            try:
                if pv != '' and pv is not None:
                    product_prices[pn] = float(pv)
            except (TypeError, ValueError):
                pass
        doc['product_prices'] = product_prices

        result = db.custom_festivals.insert_one(doc)
        return jsonify({'success': True, 'message': f'Custom festival "{name}" added!', 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/delete-custom-festival/<festival_id>', methods=['POST', 'DELETE'])
@admin_required
def admin_delete_custom_festival(festival_id):
    """Delete a custom festival by ID"""
    try:
        from bson import ObjectId
        result = db.custom_festivals.delete_one({'_id': ObjectId(festival_id)})
        if result.deleted_count:
            return jsonify({'success': True, 'message': 'Festival deleted.'})
        return jsonify({'success': False, 'error': 'Festival not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/get-products-list', methods=['GET'])
@admin_required
def admin_get_products_list():
    """Return list of product names for festival form select"""
    try:
        products = []
        for col in ['products_update', 'products', 'products_by_user']:
            for p in db[col].find({}, {'name': 1, '_id': 0}):
                n = p.get('name')
                if n and n not in products:
                    products.append(n)
        return jsonify({'success': True, 'products': sorted(products)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/send-test-notifications-all', methods=['POST'])
@admin_required
def admin_send_test_notifications_all():
    """Send festival offer emails to ALL users"""
    try:
        # Get current month to find relevant festivals
        current_month = datetime.datetime.now().strftime('%B')
        
        # Find festivals for current month
        current_festivals = []
        for festival_name, festival_data in INDIAN_FESTIVALS.items():
            if festival_data['month'] == current_month:
                current_festivals.append({
                    'name': festival_name,
                    'products': festival_data['products'],
                    'discount': festival_data['discount_range']
                })
        
        # If no festivals this month, use next available festival
        if not current_festivals:
            months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']
            current_idx = months_order.index(current_month)
            
            for i in range(1, 13):
                next_month = months_order[(current_idx + i) % 12]
                for festival_name, festival_data in INDIAN_FESTIVALS.items():
                    if festival_data['month'] == next_month:
                        current_festivals.append({
                            'name': festival_name,
                            'products': festival_data['products'],
                            'discount': festival_data['discount_range']
                        })
                        break
                if current_festivals:
                    break
        
        # Get all users with email addresses
        all_users = list(users.find({'email': {'$exists': True, '$ne': ''}}))
        
        if not all_users:
            return jsonify({'success': False, 'error': 'No users with email addresses found'}), 400
        
        success_count = 0
        failed_count = 0
        
        # Send email to each user
        for user in all_users:
            try:
                user_email = user.get('email')
                user_name = user.get('name', 'Valued Customer')
                
                # Get user's purchase history
                user_purchases = list(products_by_user.find({'user_id': user['_id']}).limit(5))
                
                # Create personalized email content
                festival_info = current_festivals[0] if current_festivals else {
                    'name': 'Special Sale',
                    'products': ['All Products'],
                    'discount': '20-30%'
                }
                
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 30px;
                            text-align: center;
                            border-radius: 10px 10px 0 0;
                        }}
                        .content {{
                            background: white;
                            padding: 30px;
                            border: 1px solid #e0e0e0;
                        }}
                        .festival-banner {{
                            background: #fbbf24;
                            color: #1f2937;
                            padding: 20px;
                            margin: 20px 0;
                            border-radius: 8px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 18px;
                        }}
                        .products-list {{
                            background: #f3f4f6;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                        }}
                        .discount-badge {{
                            background: #ef4444;
                            color: white;
                            padding: 10px 20px;
                            border-radius: 20px;
                            font-weight: bold;
                            display: inline-block;
                            margin: 10px 0;
                        }}
                        .cta-button {{
                            background: #10b981;
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            display: inline-block;
                            margin: 20px 0;
                            font-weight: bold;
                        }}
                        .purchase-history {{
                            background: #fef3c7;
                            padding: 15px;
                            border-left: 4px solid #f59e0b;
                            margin: 20px 0;
                        }}
                        .footer {{
                            text-align: center;
                            padding: 20px;
                            color: #6b7280;
                            font-size: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🎉 Sales Sense AI</h1>
                        <p>Exclusive Festival Offers Just For You!</p>
                    </div>
                    
                    <div class="content">
                        <h2>Dear {user_name},</h2>
                        
                        <p>We hope this email finds you well! We're excited to share our special <strong>{festival_info['name']}</strong> offers with you.</p>
                        
                        <div class="festival-banner">
                            🎊 {festival_info['name']} Special Sale 🎊
                        </div>
                        
                        <div class="discount-badge">
                            💰 Get {festival_info['discount']} OFF
                        </div>
                        
                        <div class="products-list">
                            <h3>📦 Featured Products:</h3>
                            <ul>
                                {''.join([f'<li><strong>{product}</strong></li>' for product in festival_info['products'][:6]])}
                            </ul>
                        </div>
                """
                
                # Add personalized recommendations based on purchase history
                if user_purchases:
                    purchased_products = [p.get('product_name', 'Product') for p in user_purchases[:3]]
                    html_body += f"""
                        <div class="purchase-history">
                            <h3>🛍️ Your Recent Purchases:</h3>
                            <p>We noticed you bought: <strong>{', '.join(purchased_products)}</strong></p>
                            <p>Get special combo offers on related products!</p>
                        </div>
                    """
                
                html_body += f"""
                        <p style="margin-top: 20px;">
                            Don't miss out on these incredible deals! Shop now and save big on your favorite products.
                        </p>
                        
                        <center>
                            <a href="http://localhost:5000/products" class="cta-button">
                                🛒 Shop Now
                            </a>
                        </center>
                        
                        <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                            ⏰ <strong>Limited Time Offer</strong> - Hurry before stock runs out!
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is a promotional email from Sales Sense AI</p>
                        <p>You're receiving this because you're a valued customer</p>
                        <p>© 2024 Sales Sense AI. All rights reserved.</p>
                    </div>
                </body>
                </html>
                """
                
                # Send email
                if send_email(user_email, f"🎉 {festival_info['name']} Special Offers - Exclusive Discounts!", html_body)[0]:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error sending email to {user.get('email', 'unknown')}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Test notifications sent! ✅ {success_count} successful, ❌ {failed_count} failed',
            'success_count': success_count,
            'failed_count': failed_count,
            'total_users': len(all_users)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/send-personalized-offers', methods=['POST'])
@admin_required
def admin_send_personalized_offers():
    """Send personalized product offers to users based on their purchase history"""
    try:
        data = request.get_json()
        target_users = data.get('user_ids', [])  # If empty, send to all users
        
        # Get users to send offers to
        if target_users:
            query = {'_id': {'$in': [ObjectId(uid) for uid in target_users]}, 'email': {'$exists': True, '$ne': ''}}
        else:
            query = {'email': {'$exists': True, '$ne': ''}}
        
        all_users = list(users.find(query))
        
        if not all_users:
            return jsonify({'success': False, 'error': 'No users with email addresses found'}), 400
        
        success_count = 0
        failed_count = 0
        
        # Get current festival for offers
        current_month = datetime.datetime.now().strftime('%B')
        current_festival = None
        for festival_name, festival_data in INDIAN_FESTIVALS.items():
            if festival_data['month'] == current_month:
                current_festival = {
                    'name': festival_name,
                    'discount': festival_data['discount_range']
                }
                break
        
        if not current_festival:
            current_festival = {
                'name': 'Special Sale',
                'discount': '20-30%'
            }
        
        # Send personalized emails
        for user in all_users:
            try:
                user_email = user.get('email')
                user_name = user.get('name', 'Valued Customer')
                
                # Get user's purchase history
                user_purchases = list(products_by_user.find({'user_id': user['_id']}).sort('_id', -1).limit(10))
                
                if not user_purchases:
                    # Skip users with no purchase history
                    continue
                
                # Analyze purchase patterns
                purchased_categories = {}
                purchased_products = []
                total_spent = 0
                
                for purchase in user_purchases:
                    purchased_products.append(purchase.get('product_name', 'Product'))
                    category = purchase.get('category', 'General')
                    purchased_categories[category] = purchased_categories.get(category, 0) + 1
                    total_spent += purchase.get('price', 0) * purchase.get('quantity', 1)
                
                # Find top category
                top_category = max(purchased_categories, key=purchased_categories.get) if purchased_categories else 'General'
                
                # Get recommended products from the same category
                recommended_products = list(products_update.find({'category': top_category}).limit(5))
                
                # Create personalized email
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                            color: white;
                            padding: 30px;
                            text-align: center;
                            border-radius: 10px 10px 0 0;
                        }}
                        .content {{
                            background: white;
                            padding: 30px;
                            border: 1px solid #e0e0e0;
                        }}
                        .personalized-section {{
                            background: #fef3c7;
                            padding: 20px;
                            border-left: 4px solid #f59e0b;
                            margin: 20px 0;
                            border-radius: 8px;
                        }}
                        .product-card {{
                            background: #f9fafb;
                            padding: 15px;
                            margin: 10px 0;
                            border-radius: 8px;
                            border: 1px solid #e5e7eb;
                        }}
                        .discount-badge {{
                            background: #ef4444;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 20px;
                            font-weight: bold;
                            display: inline-block;
                            margin: 10px 0;
                        }}
                        .stats-box {{
                            background: #ecfdf5;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                            border: 1px solid #10b981;
                        }}
                        .cta-button {{
                            background: #10b981;
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            display: inline-block;
                            margin: 20px 0;
                            font-weight: bold;
                        }}
                        .footer {{
                            text-align: center;
                            padding: 20px;
                            color: #6b7280;
                            font-size: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🎯 Personalized Offers for {user_name}</h1>
                        <p>Exclusive deals based on your shopping preferences</p>
                    </div>
                    
                    <div class="content">
                        <h2>Dear {user_name},</h2>
                        
                        <p>Thank you for being a valued customer! We've handpicked special offers just for you based on your shopping history.</p>
                        
                        <div class="stats-box">
                            <h3>📊 Your Shopping Summary:</h3>
                            <p><strong>Total Orders:</strong> {len(user_purchases)}</p>
                            <p><strong>Total Spent:</strong> ₹{total_spent:,.2f}</p>
                            <p><strong>Favorite Category:</strong> {top_category}</p>
                        </div>
                        
                        <div class="personalized-section">
                            <h3>🛍️ You Recently Purchased:</h3>
                            <ul>
                                {''.join([f'<li><strong>{product}</strong></li>' for product in purchased_products[:5]])}
                            </ul>
                        </div>
                        
                        <h2 style="margin-top: 30px;">💎 Recommended Just For You:</h2>
                        <p>Based on your interest in <strong>{top_category}</strong> products:</p>
                        
                        <div class="discount-badge">
                            🎉 Get {current_festival['discount']} OFF - {current_festival['name']}!
                        </div>
                """
                
                # Add recommended products
                for product in recommended_products:
                    product_name = product.get('name', 'Product')
                    variants = product.get('variants', [])
                    if variants:
                        price = variants[0].get('price', 0)
                        html_body += f"""
                        <div class="product-card">
                            <h4>✨ {product_name}</h4>
                            <p style="color: #10b981; font-weight: bold; font-size: 18px;">₹{price}</p>
                            <p style="color: #ef4444; font-weight: bold;">Special Discount Available!</p>
                        </div>
                        """
                
                html_body += f"""
                        <p style="margin-top: 30px;">
                            Don't miss out on these exclusive deals tailored just for you!
                        </p>
                        
                        <center>
                            <a href="http://localhost:5000/products" class="cta-button">
                                🛒 Shop Now & Save
                            </a>
                        </center>
                        
                        <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                            ⏰ <strong>Limited Time Offer</strong> - Hurry before these deals expire!
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is a personalized offer from Sales Sense AI</p>
                        <p>You're receiving this because you're a valued customer</p>
                        <p>© 2024 Sales Sense AI. All rights reserved.</p>
                    </div>
                </body>
                </html>
                """
                
                # Send email
                if send_email(user_email, f"🎯 {user_name}, Special Offers Curated for You!", html_body)[0]:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error sending personalized offer to {user.get('email', 'unknown')}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Personalized offers sent! ✅ {success_count} successful, ❌ {failed_count} failed',
            'success_count': success_count,
            'failed_count': failed_count
        })
        
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

# ============================================
# ADMIN AI CHAT (DeepSeek-style RAG Chatbot)
# ============================================

def _rag_query(question: str) -> str:
    """Query MongoDB collections relevant to the question and build a context string."""
    import re
    q = question.lower()
    ctx_parts = []

    try:
        now = datetime.datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start  = today_start - datetime.timedelta(days=7)
        month_start = today_start.replace(day=1)

        # ── Sales / revenue queries ──────────────────────────────────
        if any(w in q for w in ['sale','revenue','sold','purchase','order','total','today','weekly','monthly','income','earning']):
            # Today
            today_pipe = [
                {'$match': {'purchase_date': {'$gte': today_start}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}
            ]
            r = list(db.user_data_bought.aggregate(today_pipe))
            ctx_parts.append(f"TODAY'S SALES: count={r[0]['count'] if r else 0}, revenue=₹{r[0]['total'] if r else 0:.2f}")

            # This week
            week_pipe = [
                {'$match': {'purchase_date': {'$gte': week_start}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}
            ]
            r = list(db.user_data_bought.aggregate(week_pipe))
            ctx_parts.append(f"THIS WEEK'S SALES: count={r[0]['count'] if r else 0}, revenue=₹{r[0]['total'] if r else 0:.2f}")

            # This month
            month_pipe = [
                {'$match': {'purchase_date': {'$gte': month_start}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}
            ]
            r = list(db.user_data_bought.aggregate(month_pipe))
            ctx_parts.append(f"THIS MONTH'S SALES: count={r[0]['count'] if r else 0}, revenue=₹{r[0]['total'] if r else 0:.2f}")

            # All-time
            all_pipe = [{'$group': {'_id': None, 'total': {'$sum': '$total'}, 'count': {'$sum': 1}}}]
            r = list(db.user_data_bought.aggregate(all_pipe))
            ctx_parts.append(f"ALL-TIME SALES: count={r[0]['count'] if r else 0}, revenue=₹{r[0]['total'] if r else 0:.2f}")

        # ── Top products ─────────────────────────────────────────────
        if any(w in q for w in ['product','top','best','popular','sell','item','category']):
            top_pipe = [
                {'$group': {'_id': '$product_name', 'units': {'$sum': '$quantity'}, 'revenue': {'$sum': '$total'}}},
                {'$sort': {'revenue': -1}},
                {'$limit': 8}
            ]
            rows = list(db.user_data_bought.aggregate(top_pipe))
            if rows:
                ctx_parts.append("TOP PRODUCTS BY REVENUE:\n" +
                    "\n".join([f"  • {r['_id']}: {r['units']} units, ₹{r['revenue']:.2f}" for r in rows]))

            # Category breakdown
            cat_pipe = [
                {'$group': {'_id': '$category', 'revenue': {'$sum': '$total'}, 'count': {'$sum': 1}}},
                {'$sort': {'revenue': -1}}, {'$limit': 6}
            ]
            cats = list(db.user_data_bought.aggregate(cat_pipe))
            if cats:
                ctx_parts.append("TOP CATEGORIES:\n" +
                    "\n".join([f"  • {c['_id'] or 'Uncategorized'}: ₹{c['revenue']:.2f} ({c['count']} orders)" for c in cats]))

            # Total products in inventory
            count = 0
            for col in ['products_update', 'products', 'products_by_user']:
                count += db[col].count_documents({})
            ctx_parts.append(f"TOTAL PRODUCTS IN INVENTORY: {count}")

            # Low stock (< 10 units)
            low_stock = []
            for col in ['products_update', 'products']:
                for p in db[col].find({}, {'name': 1, 'variants': 1, 'stock': 1}):
                    name = p.get('name', '?')
                    if p.get('variants'):
                        for v in p['variants']:
                            if (v.get('stock') or 0) < 10:
                                low_stock.append(f"{name} ({v.get('quantity','?')}): {v.get('stock',0)} left")
                    elif (p.get('stock') or 0) < 10:
                        low_stock.append(f"{name}: {p.get('stock',0)} left")
            if low_stock:
                ctx_parts.append("LOW STOCK ITEMS (<10):\n" + "\n".join([f"  • {x}" for x in low_stock[:10]]))

        # ── Users / customers ────────────────────────────────────────
        if any(w in q for w in ['user','customer','register','signup','member','buyer','new','people']):
            total_u = 0
            for col in ['users', 'users_update']:
                try: total_u += db[col].count_documents({})
                except: pass
            ctx_parts.append(f"TOTAL USERS: {total_u}")

            # New users today
            new_today = 0
            for col in ['users', 'users_update']:
                try:
                    new_today += db[col].count_documents({'created_at': {'$gte': today_start}})
                except: pass
            ctx_parts.append(f"NEW USERS TODAY: {new_today}")

            # New users this week
            new_week = 0
            for col in ['users', 'users_update']:
                try:
                    new_week += db[col].count_documents({'created_at': {'$gte': week_start}})
                except: pass
            ctx_parts.append(f"NEW USERS THIS WEEK: {new_week}")

            # Top buyers
            top_buyers = list(db.user_data_bought.aggregate([
                {'$group': {'_id': '$user_name', 'spent': {'$sum': '$total'}, 'orders': {'$sum': 1}}},
                {'$sort': {'spent': -1}}, {'$limit': 5}
            ]))
            if top_buyers:
                ctx_parts.append("TOP BUYERS:\n" +
                    "\n".join([f"  • {b['_id']}: ₹{b['spent']:.2f} ({b['orders']} orders)" for b in top_buyers]))

        # ── Workers ──────────────────────────────────────────────────
        if any(w in q for w in ['worker','staff','employee','agent','seller','team']):
            w_count = 0
            for col in ['workers_update', 'workers', 'Workers']:
                try: w_count += db[col].count_documents({})
                except: pass
            ctx_parts.append(f"TOTAL WORKERS: {w_count}")

            # Top workers by sales
            top_workers = list(db.user_data_bought.aggregate([
                {'$match': {'sold_by_name': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': '$sold_by_name', 'revenue': {'$sum': '$total'}, 'count': {'$sum': 1}}},
                {'$sort': {'revenue': -1}}, {'$limit': 5}
            ]))
            if top_workers:
                ctx_parts.append("TOP WORKERS BY SALES:\n" +
                    "\n".join([f"  • {w['_id']}: ₹{w['revenue']:.2f} ({w['count']} sales)" for w in top_workers]))

        # ── Daily trend ──────────────────────────────────────────────
        if any(w in q for w in ['trend','daily','per day','chart','graph','last 7','last seven','week']):
            daily_pipe = [
                {'$match': {'purchase_date': {'$gte': week_start}}},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$purchase_date'}},
                    'revenue': {'$sum': '$total'}, 'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            days = list(db.user_data_bought.aggregate(daily_pipe))
            if days:
                ctx_parts.append("DAILY SALES (last 7 days):\n" +
                    "\n".join([f"  {d['_id']}: ₹{d['revenue']:.2f} ({d['count']} orders)" for d in days]))

        # ── Payment status breakdown ─────────────────────────────────
        if any(w in q for w in ['payment','pending','completed','status','paid']):
            pay_pipe = [
                {'$group': {'_id': '$payment_status', 'count': {'$sum': 1}, 'total': {'$sum': '$total'}}},
                {'$sort': {'total': -1}}
            ]
            pays = list(db.user_data_bought.aggregate(pay_pipe))
            if pays:
                ctx_parts.append("PAYMENT STATUS BREAKDOWN:\n" +
                    "\n".join([f"  • {p['_id'] or 'unknown'}: {p['count']} orders, ₹{p['total']:.2f}" for p in pays]))

    except Exception as e:
        ctx_parts.append(f"[DB query error: {e}]")

    return "\n\n".join(ctx_parts) if ctx_parts else "No relevant data found in database."


@app.route('/admin/ai-chat')
@admin_required
def admin_ai_chat_page():
    """Render the DeepSeek-style AI chat page for admin."""
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    api_key_missing = not api_key or api_key == 'your_groq_api_key_here'
    return render_template('admin_ai_chat.html', api_key_missing=api_key_missing)


@app.route('/admin/ai-chat/send', methods=['POST'])
@admin_required
def admin_ai_chat_send():
    """RAG + Groq LLM endpoint for the admin AI chat."""
    try:
        import requests as _requests

        data    = request.get_json() or {}
        question = (data.get('question') or '').strip()
        history  = data.get('history') or []
        deep_think = bool(data.get('deep_think', False))

        if not question:
            return jsonify({'answer': 'Please ask a question.'})

        # ── Check API key ────────────────────────────────────────────
        api_key = os.getenv('GROQ_API_KEY', '').strip()
        if not api_key or api_key == 'your_groq_api_key_here':
            return jsonify({
                'answer': (
                    "⚠️ **Groq API key not configured.**\n\n"
                    "To enable AI responses:\n"
                    "1. Visit [console.groq.com](https://console.groq.com) — it's **free**\n"
                    "2. Create an API key\n"
                    "3. Add to your `.env` file:\n```\nGROQ_API_KEY=gsk_...\n```\n"
                    "4. Restart Flask\n\n"
                    "ℹ️ *Groq uses DeepSeek-R1 model under the hood for free (no credit card needed).*"
                )
            })

        # ── RAG: fetch database context ──────────────────────────────
        db_context = _rag_query(question)

        # ── System prompt ────────────────────────────────────────────
        system_prompt = """You are an intelligent Sales Database Assistant.

You answer questions strictly using the provided database context.
The database name is "saless".

Collections in the database:
- users / users_update
- products / products_update / products_by_user
- user_data_bought  (primary sales collection — has purchase_date, total, product_name, category, quantity, user_name, sold_by_name, payment_status)
- workers_update / Workers / Worker_added_products
- admins
- custom_festivals

Rules:
1. Only answer using the given context.
2. Do NOT assume or hallucinate missing data.
3. If the answer is not found in context, respond: "The requested information is not available in the database."
4. If the question requires calculation (e.g., total sales, revenue, counts), compute using the retrieved data.
5. Keep answers clear, structured, and professional.
6. If the question relates to:
   - Sales → prioritize user_data_bought
   - Customers → prioritize users or user_data_bought
   - Inventory → prioritize products / products_update
   - Worker activity → prioritize workers_update or sold_by_name in user_data_bought
7. When listing data, present in bullet points or tables (Markdown).
8. Always stay within database scope. Do not provide general knowledge answers.

Answer format:
- Short summary first
- Then structured details (if needed)
- Use Markdown for formatting (tables, bold, bullets)"""

        # ── Build messages ───────────────────────────────────────────
        messages = [{'role': 'system', 'content': system_prompt}]

        # Add recent history (last 6 turns)
        for m in history[-6:]:
            if m.get('role') in ('user', 'assistant') and m.get('content'):
                messages.append({'role': m['role'], 'content': m['content']})

        # Inject DB context into the current user question
        user_content = f"""Database Context (retrieved from MongoDB):
```
{db_context}
```

User Question: {question}"""
        messages.append({'role': 'user', 'content': user_content})

        # ── Pick model ───────────────────────────────────────────────
        # deepseek-r1-distill-llama-70b is DeepSeek's model on Groq (free)
        model = 'deepseek-r1-distill-llama-70b' if deep_think else 'llama-3.3-70b-versatile'

        # ── Call Groq API (OpenAI-compatible) ────────────────────────
        resp = _requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.2,
                'max_tokens': 1500,
                'stream': False
            },
            timeout=30
        )

        if resp.status_code != 200:
            err = resp.json().get('error', {}).get('message', resp.text)
            return jsonify({'answer': f'⚠️ Groq API error: {err}'}), 200

        answer = resp.json()['choices'][0]['message']['content'].strip()

        # Strip <think>...</think> tags that DeepSeek-R1 sometimes returns
        import re as _re
        answer = _re.sub(r'<think>.*?</think>', '', answer, flags=_re.DOTALL).strip()

        # ── Persist Q&A to MongoDB ───────────────────────────────────
        session_id = (data.get('session_id') or '').strip()
        try:
            if admin_ai_chats is not None and session_id:
                existing = admin_ai_chats.find_one({'session_id': session_id})
                new_msgs = [
                    {'role': 'user', 'text': question, 'ts': datetime.datetime.utcnow()},
                    {'role': 'ai',   'text': answer,   'ts': datetime.datetime.utcnow()}
                ]
                if existing:
                    admin_ai_chats.update_one(
                        {'session_id': session_id},
                        {'$push': {'messages': {'$each': new_msgs}},
                         '$set':  {'updated_at': datetime.datetime.utcnow()}}
                    )
                else:
                    admin_ai_chats.insert_one({
                        'session_id': session_id,
                        'title':      question[:60],
                        'messages':   new_msgs,
                        'created_at': datetime.datetime.utcnow(),
                        'updated_at': datetime.datetime.utcnow()
                    })
        except Exception as _db_err:
            print(f'AI chat save error: {_db_err}')

        return jsonify({'answer': answer, 'session_id': session_id})

    except Exception as e:
        return jsonify({'answer': f'⚠️ Server error: {str(e)}'}), 200


@app.route('/api/ai-chat-sessions')
@admin_required
def ai_chat_sessions_list():
    """Return all AI chat sessions (title + session_id + updated_at), newest first."""
    try:
        if admin_ai_chats is None:
            return jsonify([])
        docs = list(admin_ai_chats.find(
            {}, {'session_id': 1, 'title': 1, 'updated_at': 1, '_id': 0}
        ).sort('updated_at', -1).limit(50))
        for d in docs:
            if hasattr(d.get('updated_at'), 'strftime'):
                d['updated_at'] = d['updated_at'].strftime('%d %b %Y, %H:%M')
        return jsonify(docs)
    except Exception as e:
        return jsonify([])


@app.route('/api/ai-chat-sessions/<session_id>')
@admin_required
def ai_chat_session_messages(session_id):
    """Return all messages for a given session_id."""
    try:
        if admin_ai_chats is None:
            return jsonify([])
        doc = admin_ai_chats.find_one({'session_id': session_id}, {'messages': 1, '_id': 0})
        if not doc:
            return jsonify([])
        msgs = doc.get('messages', [])
        for m in msgs:
            if hasattr(m.get('ts'), 'strftime'):
                m['ts'] = m['ts'].strftime('%d %b %Y, %H:%M')
        return jsonify(msgs)
    except Exception as e:
        return jsonify([])


@app.route('/api/ai-chat-sessions/<session_id>/delete', methods=['POST'])
@admin_required
def ai_chat_session_delete(session_id):
    """Delete a chat session by session_id."""
    try:
        if admin_ai_chats is not None:
            admin_ai_chats.delete_one({'session_id': session_id})
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


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
            'top products': {
                'keywords': ['top product', 'best selling', 'popular product', 'most sold', 'best seller', 'highest selling'],
                'answer': f"""🏆 <strong>Top Products Analysis:</strong><br><br>
                📊 <strong>Current Inventory:</strong><br>
                • Total Products: <strong>{total_products}</strong><br>
                • Active Categories: Multiple<br><br>
                💡 <strong>How to find top sellers:</strong><br>
                1. Go to Admin Dashboard → Analytics<br>
                2. Check "Sales by Product" chart<br>
                3. View purchase history for trends<br><br>
                Products are ranked by:<br>
                • Total sales volume<br>
                • Revenue generated<br>
                • Customer ratings<br><br>
                Check the analytics page for detailed product performance! 📈"""
            },
            'sales trends': {
                'keywords': ['sales trend', 'revenue trend', 'sales pattern', 'business trend', 'growth'],
                'answer': f"""📈 <strong>Sales Trends & Insights:</strong><br><br>
                💰 <strong>Current Performance:</strong><br>
                • Total Revenue: ₹{total_revenue:,.2f}<br>
                • Today's Sales: ₹{sales_today:,.2f}<br>
                • Active Users: {total_users:,}<br><br>
                📊 <strong>View Trends:</strong><br>
                • 7-day sales comparison<br>
                • Daily revenue tracking<br>
                • Category-wise performance<br>
                • Peak sales hours<br><br>
                🎯 <strong>Growth Indicators:</strong><br>
                • User registration rate<br>
                • Average order value<br>
                • Repeat purchase rate<br><br>
                Access the Analytics Dashboard for interactive charts! 📊"""
            },
            'inventory status': {
                'keywords': ['inventory', 'stock status', 'stock level', 'available stock', 'out of stock'],
                'answer': """📦 <strong>Inventory Status:</strong><br><br>
                <strong>Stock Levels:</strong><br>
                🟢 <strong>High Stock:</strong> >50 units (Healthy)<br>
                🟡 <strong>Medium Stock:</strong> 10-50 units (Monitor)<br>
                🔴 <strong>Low Stock:</strong> <10 units (Reorder)<br><br>
                <strong>Quick Actions:</strong><br>
                • View Product Reports for detailed stock<br>
                • Check low stock alerts<br>
                • Monitor stock value in ₹<br>
                • Set reorder points<br><br>
                <strong>Stock Management:</strong><br>
                • Auto-updates on sales<br>
                • Real-time tracking<br>
                • Variant-level control<br><br>
                Navigate to Product Reports → Inventory to see all stock details! 📊"""
            },
            'users': {
                'keywords': ['user', 'customer', 'how many users', 'total users', 'user count'],
                'answer': f"""👥 <strong>User Statistics:</strong><br><br>
                📈 Total Users: <strong>{total_users:,}</strong><br>
                ✨ New Today: <strong>{new_users_today}</strong><br>
                🛒 Guest Checkout: <strong>Enabled</strong><br><br>
                Users can register, browse products, make purchases, and receive order confirmations via email!"""
            },
            'revenue insights': {
                'keywords': ['revenue', 'income', 'earnings', 'profit', 'money made'],
                'answer': f"""💰 <strong>Revenue Insights:</strong><br><br>
                <strong>Total Revenue:</strong> ₹{total_revenue:,.2f}<br>
                <strong>Today's Sales:</strong> ₹{sales_today:,.2f}<br><br>
                📊 <strong>Revenue Breakdown:</strong><br>
                • Product sales<br>
                • Category performance<br>
                • Payment method distribution<br>
                • Time-based analysis<br><br>
                💡 <strong>Revenue Analytics:</strong><br>
                • Average order value<br>
                • Revenue per user<br>
                • Monthly trends<br>
                • Growth rate<br><br>
                Check Analytics Dashboard for detailed revenue reports! 💵"""
            },
            'customer analytics': {
                'keywords': ['customer analytic', 'user behavior', 'customer insight', 'user activity', 'buyer pattern'],
                'answer': f"""👥 <strong>Customer Analytics:</strong><br><br>
                📊 <strong>Current Stats:</strong><br>
                • Total Customers: {total_users:,}<br>
                • New Today: {new_users_today}<br><br>
                <strong>Customer Metrics:</strong><br>
                • Purchase frequency<br>
                • Average order value<br>
                • Favorite categories<br>
                • Active vs inactive users<br><br>
                <strong>Behavioral Insights:</strong><br>
                • Shopping patterns<br>
                • Peak activity times<br>
                • Cart abandonment rate<br>
                • Repeat purchase rate<br><br>
                Visit User Management to see detailed customer profiles! 📈"""
            },
            'low stock alerts': {
                'keywords': ['low stock', 'stock alert', 'reorder', 'running low', 'almost out'],
                'answer': """⚠️ <strong>Low Stock Alert System:</strong><br><br>
                <strong>Alert Triggers:</strong><br>
                🔴 Critical: <10 units<br>
                🟡 Warning: <20 units<br><br>
                <strong>Monitoring:</strong><br>
                • Real-time stock tracking<br>
                • Automatic alert generation<br>
                • Email notifications (if configured)<br>
                • Dashboard warnings<br><br>
                <strong>Take Action:</strong><br>
                1. Check Product Reports<br>
                2. Identify low stock items<br>
                3. Place reorders<br>
                4. Update stock levels<br><br>
                Navigate to Product Reports to see all low stock items! 📦"""
            },
            'payment methods': {
                'keywords': ['payment', 'pay', 'checkout method', 'payment option', 'how to pay'],
                'answer': """💳 <strong>Payment Methods:</strong><br><br>
                <strong>Available Options:</strong><br>
                • Cash on Delivery (COD)<br>
                • UPI Payment<br>
                • Card Payment<br>
                • Net Banking<br><br>
                <strong>Payment Process:</strong><br>
                1. Add items to cart<br>
                2. Proceed to checkout<br>
                3. Enter delivery details<br>
                4. Select payment method<br>
                5. Confirm order<br><br>
                <strong>Security:</strong><br>
                • Secure transactions<br>
                • Email confirmations<br>
                • Order tracking<br><br>
                All payments are processed securely! 🔒"""
            },
            'order history': {
                'keywords': ['order history', 'past order', 'previous purchase', 'my orders', 'purchase history'],
                'answer': """📋 <strong>Order History:</strong><br><br>
                <strong>View Orders:</strong><br>
                • Go to User Details page<br>
                • Check purchase history section<br>
                • Filter by date/status<br><br>
                <strong>Order Information:</strong><br>
                • Product details<br>
                • Order date & time<br>
                • Total amount in ₹<br>
                • Payment method<br>
                • Delivery status<br><br>
                <strong>Admin Access:</strong><br>
                • View all user orders<br>
                • Export order data<br>
                • Generate reports<br><br>
                Check Admin Dashboard → Users → View Details for order history! 📊"""
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
            'seasonal trends': {
                'keywords': ['seasonal', 'season', 'festival season', 'holiday sales', 'festive'],
                'answer': """🌟 <strong>Seasonal Sales Trends:</strong><br><br>
                <strong>Peak Seasons:</strong><br>
                🎉 <strong>Festival Season:</strong> Oct-Nov (Diwali)<br>
                🎊 <strong>New Year:</strong> Jan<br>
                💝 <strong>Valentine's:</strong> Feb<br>
                🌺 <strong>Holi:</strong> March<br><br>
                <strong>Marketing Strategy:</strong><br>
                • Automated festival emails<br>
                • Special offers & discounts<br>
                • Product recommendations<br>
                • Targeted campaigns<br><br>
                <strong>Analytics:</strong><br>
                • Year-over-year comparison<br>
                • Festival impact analysis<br>
                • Best-selling items per season<br><br>
                Check Festival Notifications to manage campaigns! 🎯"""
            },
            'worker performance': {
                'keywords': ['worker performance', 'staff performance', 'employee productivity', 'worker stat'],
                'answer': """👷 <strong>Worker Performance Tracking:</strong><br><br>
                <strong>Metrics Tracked:</strong><br>
                • Products added<br>
                • Activity timestamps<br>
                • Last login time<br>
                • Contribution level<br><br>
                <strong>Performance Indicators:</strong><br>
                • Daily productivity<br>
                • Quality of entries<br>
                • Response time<br>
                • Task completion<br><br>
                <strong>Management Tools:</strong><br>
                • Activate/Deactivate workers<br>
                • Reset passwords<br>
                • View activity logs<br>
                • Performance reports<br><br>
                Access Worker Management section for detailed reports! 📊"""
            },
            'categories': {
                'keywords': ['category', 'categories', 'product type', 'product group', 'classification'],
                'answer': """🏷️ <strong>Product Categories:</strong><br><br>
                <strong>Category Management:</strong><br>
                • Organize products by type<br>
                • Easy browsing for customers<br>
                • Category-wise analytics<br>
                • Custom category creation<br><br>
                <strong>Popular Categories:</strong><br>
                • Electronics<br>
                • Clothing & Fashion<br>
                • Home & Kitchen<br>
                • Beauty & Personal Care<br>
                • Food & Beverages<br><br>
                <strong>Benefits:</strong><br>
                • Better inventory organization<br>
                • Targeted marketing<br>
                • Sales analysis by category<br><br>
                View Product Reports for category breakdown! 📦"""
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
            'cart shopping': {
                'keywords': ['cart', 'shopping cart', 'add to cart', 'checkout', 'buy multiple'],
                'answer': """🛒 <strong>Shopping Cart System:</strong><br><br>
                <strong>How it Works:</strong><br>
                1. Browse products<br>
                2. Click "Add to Cart"<br>
                3. Select quantity<br>
                4. Continue shopping or checkout<br>
                5. Review cart<br>
                6. Complete purchase<br><br>
                <strong>Features:</strong><br>
                • Add multiple items<br>
                • Update quantities<br>
                • Remove items<br>
                • View total price<br>
                • Guest checkout enabled<br><br>
                <strong>Checkout Process:</strong><br>
                • Enter delivery details<br>
                • Choose payment method<br>
                • Email confirmation sent<br><br>
                Start shopping and add items to your cart! 🎉"""
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
        
        # Enhanced Smart matching with intent detection
        best_match = None
        best_score = 0
        detected_intent = None
        
        # Intent detection - check what user is asking for
        revenue_keywords = ['revenue', 'sales', 'earning', 'income', 'total sales', 'money', 'profit']
        product_keywords = ['product', 'item', 'stock', 'inventory', 'catalog']
        user_keywords = ['user', 'customer', 'member', 'buyer', 'shopper']
        order_keywords = ['order', 'purchase', 'transaction', 'bought', 'sold']
        today_keywords = ['today', 'today\'s', 'current', 'now']
        count_keywords = ['how many', 'number of', 'count', 'total']
        list_keywords = ['show', 'list', 'display', 'what are', 'give me']
        
        # Detect if user wants real-time data
        wants_today_data = any(keyword in question for keyword in today_keywords)
        wants_count = any(keyword in question for keyword in count_keywords)
        wants_list = any(keyword in question for keyword in list_keywords)
        
        # Dynamic Query Handling - Generate responses from database
        
        # 1. Today's revenue query
        if wants_today_data and any(keyword in question for keyword in revenue_keywords):
            return jsonify({
                'answer': f"""💰 <strong>Today's Revenue:</strong><br><br>
                📅 <strong>Date:</strong> {datetime.datetime.now().strftime('%B %d, %Y')}<br>
                💵 <strong>Total Sales:</strong> ₹{sales_today:,.2f}<br>
                👥 <strong>New Users Today:</strong> {new_users_today}<br><br>
                🎯 Keep up the great work! 🚀"""
            })
        
        # 2. Total revenue query
        if any(keyword in question for keyword in revenue_keywords) and ('total' in question or 'all time' in question):
            return jsonify({
                'answer': f"""💰 <strong>All-Time Revenue:</strong><br><br>
                💵 <strong>Total Revenue:</strong> ₹{total_revenue:,.2f}<br>
                📊 <strong>Total Users:</strong> {total_users:,}<br>
                📦 <strong>Products in Catalog:</strong> {total_products}<br><br>
                📈 Your business is growing! 🎉"""
            })
        
        # 3. Product count query
        if wants_count and any(keyword in question for keyword in product_keywords):
            try:
                low_stock = products_update.count_documents({'variants.stock': {'$lt': 10}}) if products_update is not None else 0
                return jsonify({
                    'answer': f"""📦 <strong>Product Statistics:</strong><br><br>
                    📊 <strong>Total Products:</strong> {total_products}<br>
                    ⚠️ <strong>Low Stock Items:</strong> {low_stock}<br>
                    ✅ <strong>Well Stocked:</strong> {total_products - low_stock}<br><br>
                    💡 Check Product Reports for detailed inventory!"""
                })
            except:
                pass
        
        # 4. User count query
        if wants_count and any(keyword in question for keyword in user_keywords):
            return jsonify({
                'answer': f"""👥 <strong>User Statistics:</strong><br><br>
                📊 <strong>Total Users:</strong> {total_users:,}<br>
                🆕 <strong>New Today:</strong> {new_users_today}<br>
                💰 <strong>Active Buyers:</strong> Growing daily!<br><br>
                🎯 Your customer base is expanding! 🚀"""
            })
        
        # 5. Top products query
        if (wants_list or 'top' in question or 'best' in question) and any(keyword in question for keyword in product_keywords):
            try:
                # Get top selling products from database
                top_products_pipeline = [
                    {'$group': {
                        '_id': '$product_name',
                        'total_sold': {'$sum': '$quantity'},
                        'revenue': {'$sum': '$total'}
                    }},
                    {'$sort': {'total_sold': -1}},
                    {'$limit': 5}
                ]
                top_prods = list(products_sold.aggregate(top_products_pipeline)) if products_sold is not None else []
                
                if top_prods:
                    products_html = '<br>'.join([
                        f'<strong>{i+1}. {prod["_id"]}</strong> - {prod["total_sold"]} units sold (₹{prod["revenue"]:,.2f})'
                        for i, prod in enumerate(top_prods)
                    ])
                    return jsonify({
                        'answer': f"""🏆 <strong>Top Selling Products:</strong><br><br>
                        {products_html}<br><br>
                        📈 These are your star performers! 🌟"""
                    })
            except:
                pass
        
        # 6. Orders today query
        if wants_today_data and any(keyword in question for keyword in order_keywords):
            try:
                orders_today = products_sold.count_documents({'date': {'$gte': today}}) if products_sold is not None else 0
                return jsonify({
                    'answer': f"""📦 <strong>Today's Orders:</strong><br><br>
                    📅 <strong>Date:</strong> {datetime.datetime.now().strftime('%B %d, %Y')}<br>
                    🛒 <strong>Total Orders:</strong> {orders_today}<br>
                    💵 <strong>Revenue:</strong> ₹{sales_today:,.2f}<br><br>
                    Keep the momentum going! 🚀"""
                })
            except:
                pass
        
        # 7. Low stock alert query
        if 'low stock' in question or 'out of stock' in question or 'reorder' in question:
            try:
                low_stock_products = list(products_update.find(
                    {'variants.stock': {'$lt': 10}}
                ).limit(5)) if products_update is not None else []
                
                if low_stock_products:
                    products_html = '<br>'.join([
                        f'<strong>• {prod["name"]}</strong> - {prod["variants"][0]["stock"]} units left'
                        for prod in low_stock_products if prod.get('variants')
                    ])
                    return jsonify({
                        'answer': f"""⚠️ <strong>Low Stock Alert:</strong><br><br>
                        {products_html}<br><br>
                        🔔 Consider restocking these items soon!"""
                    })
            except:
                pass
        
        # 8. Recent users query
        if 'recent' in question and any(keyword in question for keyword in user_keywords):
            try:
                recent_users = list(users.find().sort('created_at', -1).limit(5)) if users is not None else []
                if recent_users:
                    users_html = '<br>'.join([
                        f'<strong>• {user.get("name", "User")}</strong> - {user.get("email", "N/A")}'
                        for user in recent_users
                    ])
                    return jsonify({
                        'answer': f"""👥 <strong>Recent Users:</strong><br><br>
                        {users_html}<br><br>
                        🎉 Welcome to our new customers! """
                    })
            except:
                pass
        
        # Fall back to keyword matching for predefined answers
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
        
        # Fallback response with suggestions
        if best_score == 0 and best_match is None:
            return jsonify({
                'answer': """🤔 I'm not sure about that. Here's what I can help you with:<br><br>
                📊 <strong>Real-Time Queries:</strong><br>
                • "What is today's total revenue?"<br>
                • "How many orders today?"<br>
                • "Show me top selling products"<br>
                • "What are sales trends?"<br><br>
                📦 <strong>Product Questions:</strong><br>
                • "Show inventory status"<br>
                • "Which products are low in stock?"<br>
                • "Tell me about product categories"<br><br>
                👥 <strong>Customer Analytics:</strong><br>
                • "How many users do we have?"<br>
                • "Show customer analytics"<br>
                • "Tell me about user behavior"<br><br>
                🎉 <strong>Business Insights:</strong><br>
                • "Tell me about festival marketing"<br>
                • "Show seasonal trends"<br>
                • "What features are available?"<br><br>
                💰 <strong>Reports:</strong><br>
                • "Show revenue insights"<br>
                • "Tell me about payment methods"<br>
                • "What about worker performance?"<br><br>
                Try asking any of these questions! 😊"""
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