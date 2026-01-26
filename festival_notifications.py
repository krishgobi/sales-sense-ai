"""
Festival-Based Email Notification System for Sales Sense AI
Sends promotional emails to users 7 days before major Indian festivals
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'sales_sense')

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'your-email@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your-password')

# Indian Festivals Calendar for 2026
INDIAN_FESTIVALS_2026 = {
    'Pongal': {
        'date': datetime(2026, 1, 14),
        'name': 'Pongal',
        'description': 'Tamil harvest festival celebrating prosperity',
        'products': ['Rice', 'Milk', 'Jaggery', 'Coconut', 'Sugar Cane', 'Traditional Sweets'],
        'categories': ['Groceries', 'Fresh Produce', 'Traditional Foods', 'Food & Beverages'],
        'discount': '15-30%',
        'emoji': '🌾',
        'greeting': 'Happy Pongal!'
    },
    'Republic Day': {
        'date': datetime(2026, 1, 26),
        'name': 'Republic Day',
        'description': 'Celebrating India\'s Republic',
        'products': ['Indian Flags', 'Snacks', 'Sweets', 'Beverages', 'Party Supplies'],
        'categories': ['Festival Items', 'Snacks', 'Food & Beverages'],
        'discount': '10-20%',
        'emoji': '🇮🇳',
        'greeting': 'Happy Republic Day!'
    },
    'Holi': {
        'date': datetime(2026, 3, 14),
        'name': 'Holi',
        'description': 'Festival of colors and joy',
        'products': ['Colors', 'Gulal', 'Sweets', 'Gujiya', 'Snacks', 'Thandai', 'Water Balloons'],
        'categories': ['Festival Items', 'Sweets', 'Food & Beverages', 'Traditional Foods'],
        'discount': '15-35%',
        'emoji': '🎨',
        'greeting': 'Happy Holi!'
    },
    'Ramadan': {
        'date': datetime(2026, 3, 23),
        'name': 'Ramadan',
        'description': 'Holy month of fasting and prayer',
        'products': ['Dates', 'Dry Fruits', 'Haleem', 'Biryani', 'Traditional Sweets', 'Fruits'],
        'categories': ['Groceries', 'Traditional Foods', 'Fresh Produce', 'Food & Beverages'],
        'discount': '15-25%',
        'emoji': '🌙',
        'greeting': 'Ramadan Mubarak!'
    },
    'Eid': {
        'date': datetime(2026, 4, 22),
        'name': 'Eid-ul-Fitr',
        'description': 'Festival of breaking the fast',
        'products': ['Seviyan', 'Dates', 'Dry Fruits', 'Biryani', 'Traditional Sweets', 'Gifts'],
        'categories': ['Traditional Foods', 'Sweets', 'Food & Beverages', 'Gifts & Occasions'],
        'discount': '20-35%',
        'emoji': '🌙',
        'greeting': 'Eid Mubarak!'
    },
    'Labour Day': {
        'date': datetime(2026, 5, 1),
        'name': 'Labour Day',
        'description': 'Honoring workers and their contributions',
        'products': ['Groceries', 'Daily Essentials', 'Personal Care', 'Household Items'],
        'categories': ['Groceries', 'Personal Care', 'Household', 'Food & Beverages'],
        'discount': '10-25%',
        'emoji': '👷',
        'greeting': 'Happy Labour Day!'
    },
    'Independence Day': {
        'date': datetime(2026, 8, 15),
        'name': 'Independence Day',
        'description': 'Celebrating India\'s freedom and unity',
        'products': ['Indian Flags', 'Tricolor Items', 'Snacks', 'Sweets', 'Party Supplies'],
        'categories': ['Festival Items', 'Snacks', 'Food & Beverages', 'Party Supplies'],
        'discount': '15-30%',
        'emoji': '🇮🇳',
        'greeting': 'Happy Independence Day!'
    },
    'Ganesh Chaturthi': {
        'date': datetime(2026, 9, 2),
        'name': 'Ganesh Chaturthi',
        'description': 'Celebrating Lord Ganesha',
        'products': ['Modak', 'Coconut', 'Jaggery', 'Flowers', 'Fruits', 'Traditional Sweets'],
        'categories': ['Traditional Foods', 'Fresh Produce', 'Food & Beverages', 'Festival Items'],
        'discount': '15-30%',
        'emoji': '🐘',
        'greeting': 'Happy Ganesh Chaturthi!'
    },
    'Dussehra': {
        'date': datetime(2026, 10, 13),
        'name': 'Dussehra',
        'description': 'Victory of good over evil',
        'products': ['Sweets', 'Dry Fruits', 'Traditional Foods', 'Gifts', 'New Clothes'],
        'categories': ['Sweets', 'Traditional Foods', 'Food & Beverages', 'Gifts & Occasions'],
        'discount': '20-35%',
        'emoji': '🏹',
        'greeting': 'Happy Dussehra!'
    },
    'Diwali': {
        'date': datetime(2026, 11, 1),
        'name': 'Diwali',
        'description': 'Festival of lights and prosperity',
        'products': ['Sweets', 'Dry Fruits', 'Lamps', 'Diyas', 'Crackers', 'Gifts', 'Decorations'],
        'categories': ['Sweets', 'Traditional Foods', 'Festival Items', 'Food & Beverages', 'Gifts & Occasions'],
        'discount': '20-40%',
        'emoji': '🪔',
        'greeting': 'Happy Diwali!'
    },
    'Christmas': {
        'date': datetime(2026, 12, 25),
        'name': 'Christmas',
        'description': 'Celebrating joy and togetherness',
        'products': ['Cake', 'Plum Cake', 'Chocolate', 'Wine', 'Gifts', 'Decorations', 'Turkey'],
        'categories': ['Bakery', 'Food & Beverages', 'Gifts & Occasions', 'Party Supplies'],
        'discount': '15-35%',
        'emoji': '🎄',
        'greeting': 'Merry Christmas!'
    },
    'New Year': {
        'date': datetime(2027, 1, 1),
        'name': 'New Year',
        'description': 'Welcoming a new beginning',
        'products': ['Champagne', 'Party Snacks', 'Beverages', 'Cake', 'Decorations', 'Party Supplies'],
        'categories': ['Beverages', 'Food & Beverages', 'Party Supplies', 'Bakery'],
        'discount': '20-30%',
        'emoji': '🎉',
        'greeting': 'Happy New Year!'
    }
}

def get_upcoming_festivals(days_ahead=7):
    """Get festivals that are coming up in the specified number of days"""
    today = datetime.now()
    target_date = today + timedelta(days=days_ahead)
    
    upcoming = []
    for festival_name, festival_data in INDIAN_FESTIVALS_2026.items():
        festival_date = festival_data['date']
        days_until = (festival_date - today).days
        
        # Check if festival is exactly X days away (within a 1-day window)
        if days_ahead - 1 <= days_until <= days_ahead + 1:
            festival_info = festival_data.copy()
            festival_info['days_until'] = days_until
            upcoming.append(festival_info)
    
    return upcoming

def create_festival_email_html(user_name, festival_data, products):
    """Create HTML email content for festival promotion"""
    product_list_html = ""
    for product in products[:10]:  # Show top 10 relevant products
        # Get first variant price if variants exist
        price = 0
        if 'variants' in product and product['variants']:
            if isinstance(product['variants'], list):
                price = product['variants'][0].get('price', 0)
            else:
                price = product.get('price', 0)
        else:
            price = product.get('price', 0)
        
        product_list_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <strong>{product.get('name', 'Unknown Product')}</strong>
                <br><small>{product.get('category', 'General')}</small>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">
                <span style="color: #28a745; font-weight: bold;">₹{price:.2f}</span>
            </td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="margin: 0; font-size: 28px;">{festival_data['emoji']} {festival_data['greeting']}</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">{festival_data['name']} Special Offers!</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
            <h2 style="color: #667eea;">Dear {user_name},</h2>
            
            <p style="font-size: 16px;">
                {festival_data['name']} is just <strong>{festival_data['days_until']} days away</strong>! 
                {festival_data['description']}
            </p>
            
            <div style="background: #fff; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="margin-top: 0; color: #764ba2;">🎁 Special Festival Discount: {festival_data['discount']} OFF</h3>
                <p style="margin-bottom: 0;">Get amazing discounts on all festival essentials!</p>
            </div>
            
            <h3 style="color: #667eea;">📦 Featured Products for {festival_data['name']}:</h3>
            
            <table style="width: 100%; background: white; border-radius: 10px; overflow: hidden; margin: 20px 0;">
                {product_list_html}
            </table>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:5000/products" 
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; 
                          padding: 15px 40px; 
                          text-decoration: none; 
                          border-radius: 25px; 
                          font-weight: bold; 
                          font-size: 16px;
                          display: inline-block;">
                    🛒 Shop Now
                </a>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    ⚡ <strong>Limited Time Offer!</strong> Stock up now and save big on your favorite products.
                </p>
            </div>
            
            <p style="font-size: 14px; color: #666; margin-top: 30px;">
                Happy Shopping!<br>
                <strong>Sales Sense AI Team</strong>
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
            <p>You're receiving this email because you subscribed to festival offers from Sales Sense AI.</p>
            <p>If you wish to unsubscribe, please contact us at support@salessense.com</p>
        </div>
    </body>
    </html>
    """
    return html

def send_festival_email(user_email, user_name, festival_data, products):
    """Send festival promotional email to a user"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{festival_data['emoji']} {festival_data['name']} Special Offers - Up to {festival_data['discount']} OFF!"
        msg['From'] = SMTP_EMAIL
        msg['To'] = user_email
        
        # Create HTML content
        html_content = create_festival_email_html(user_name, festival_data, products)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"❌ Error sending email to {user_email}: {e}")
        return False

def get_festival_products(festival_data, db):
    """Get products relevant to the festival"""
    products_collection = db['products_update']
    
    # Search for products matching festival categories or product names
    query = {
        '$or': [
            {'category': {'$in': festival_data['categories']}},
            {'name': {'$regex': '|'.join(festival_data['products']), '$options': 'i'}}
        ],
        'is_active': True
    }
    
    products = list(products_collection.find(query).limit(20))
    
    # Parse variants if they're strings
    import ast
    for product in products:
        if 'variants' in product and isinstance(product['variants'], str):
            try:
                product['variants'] = ast.literal_eval(product['variants'])
            except:
                product['variants'] = []
    
    return products

def send_festival_notifications():
    """Main function to check for upcoming festivals and send notifications"""
    print(f"\n{'='*60}")
    print(f"Festival Notification Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    users_collection = db['users']
    
    # Get upcoming festivals (7 days ahead)
    upcoming_festivals = get_upcoming_festivals(days_ahead=7)
    
    if not upcoming_festivals:
        print("ℹ️  No festivals in the next 7 days.")
        client.close()
        return
    
    for festival in upcoming_festivals:
        print(f"\n🎉 Upcoming Festival: {festival['name']} ({festival['emoji']})")
        print(f"   Date: {festival['date'].strftime('%B %d, %Y')}")
        print(f"   Days until: {festival['days_until']}")
        print(f"   Discount: {festival['discount']}")
        
        # Get relevant products
        products = get_festival_products(festival, db)
        print(f"   Found {len(products)} relevant products")
        
        # Get all active users with email notifications enabled
        users = list(users_collection.find({
            'is_active': True,
            'email_notifications': {'$ne': False}
        }))
        
        print(f"   Sending emails to {len(users)} users...")
        
        success_count = 0
        for user in users:
            user_email = user.get('email', '')
            user_name = user.get('name', 'Valued Customer')
            
            if user_email and '@' in user_email:
                # In production, uncomment this to actually send emails
                # if send_festival_email(user_email, user_name, festival, products):
                #     success_count += 1
                
                # For now, just simulate
                print(f"   ✉️  Would send email to: {user_name} <{user_email}>")
                success_count += 1
        
        print(f"   ✅ Successfully sent {success_count} emails for {festival['name']}")
    
    print(f"\n{'='*60}")
    print("Festival notification check completed!")
    print(f"{'='*60}\n")
    
    client.close()

def run_notification_scheduler(check_interval_hours=24):
    """Run the notification scheduler in a background thread"""
    while True:
        try:
            send_festival_notifications()
        except Exception as e:
            print(f"❌ Error in notification scheduler: {e}")
        
        # Wait for next check (default: check once per day)
        print(f"💤 Next check in {check_interval_hours} hours...")
        time.sleep(check_interval_hours * 3600)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("FESTIVAL NOTIFICATION SYSTEM FOR SALES SENSE AI")
    print("="*60)
    
    # Run once for testing
    send_festival_notifications()
    
    # Uncomment below to run as a continuous background service
    # print("\n🔄 Starting continuous notification scheduler...")
    # run_notification_scheduler(check_interval_hours=24)
