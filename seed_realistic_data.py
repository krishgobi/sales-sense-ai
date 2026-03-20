"""
Seed realistic sample data for all collections with high sales activity.
This populates the database with meaningful data that displays on the home page.

Usage:
    python seed_realistic_data.py
"""

import os
import sys
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
def get_db_connection():
    mongo_url = os.getenv('MONGODB_URL')
    if not mongo_url:
        print("❌ Error: MONGODB_URL not found in .env")
        sys.exit(1)
    
    try:
        client = MongoClient(mongo_url)
        client.admin.command('ping')
        return client["saless"]
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        sys.exit(1)

db = get_db_connection()

# ===== SAMPLE DATA =====

TAMIL_PRODUCTS = [
    {"name": "அரிசி (Rice)", "category": "Food & Beverages", "price": 45, "stock": 100},
    {"name": "பருப்பு (Dal)", "category": "Food & Beverages", "price": 80, "stock": 80},
    {"name": "எண்ணெய் (Oil)", "category": "Food & Beverages", "price": 120, "stock": 60},
    {"name": "கோதுமை (Wheat)", "category": "Food & Beverages", "price": 50, "stock": 90},
    {"name": "சக்கரை (Sugar)", "category": "Food & Beverages", "price": 55, "stock": 75},
    {"name": "உப்பு (Salt)", "category": "Food & Beverages", "price": 25, "stock": 150},
    {"name": "பயற்றும் உளுந்து (Beans)", "category": "Food & Beverages", "price": 90, "stock": 70},
    {"name": "வெங்காயம் (Onion)", "category": "Vegetables", "price": 35, "stock": 120},
    {"name": "தக்காளி (Tomato)", "category": "Vegetables", "price": 45, "stock": 100},
    {"name": "கீரை (Spinach)", "category": "Vegetables", "price": 40, "stock": 85},
    {"name": "உருளைக்கிழங்கு (Potato)", "category": "Vegetables", "price": 30, "stock": 110},
    {"name": "வெள்ளாடை (Carrot)", "category": "Vegetables", "price": 50, "stock": 95},
    {"name": "பூக்கோஸ் (Broccoli)", "category": "Vegetables", "price": 65, "stock": 60},
    {"name": "கடுக்காய் (Spices)", "category": "Spices", "price": 150, "stock": 40},
    {"name": "மிளகு (Pepper)", "category": "Spices", "price": 180, "stock": 50},
    {"name": "உமியாறைக்கை (Turmeric)", "category": "Spices", "price": 120, "stock": 70},
    {"name": "மல்லி (Coriander)", "category": "Spices", "price": 100, "stock": 80},
    {"name": "இஞ்சி (Ginger)", "category": "Spices", "price": 60, "stock": 90},
    {"name": "பால் (Milk)", "category": "Dairy", "price": 55, "stock": 100},
    {"name": "தயிர் (Yogurt)", "category": "Dairy", "price": 40, "stock": 120},
    {"name": "வெண்ணை (Butter)", "category": "Dairy", "price": 250, "stock": 50},
    {"name": "பனீர் (Paneer)", "category": "Dairy", "price": 280, "stock": 45},
    {"name": "முந்திரி (Cashew)", "category": "Dry Fruits", "price": 450, "stock": 35},
    {"name": "பாதாம் (Almond)", "category": "Dry Fruits", "price": 380, "stock": 40},
    {"name": "உலர் திராட்சை (Raisins)", "category": "Dry Fruits", "price": 200, "stock": 60},
    {"name": "தேங்காய் (Coconut)", "category": "Dry Fruits", "price": 75, "stock": 80},
    {"name": "சுவை வாடைக் கொட்டை (Roasted Peanuts)", "category": "Snacks", "price": 120, "stock": 100},
    {"name": "சிப்ஸ் (Chips)", "category": "Snacks", "price": 45, "stock": 150},
    {"name": "மிக்ஸ்சர் (Mixer)", "category": "Snacks", "price": 90, "stock": 70},
    {"name": "க்ரீம் பிஸ்கட் (Cream Biscuits)", "category": "Snacks", "price": 55, "stock": 120},
]

FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Arun", "Divya", "Sanjay", "Neha",
               "Mohan", "Kavya", "Arjun", "Pooja", "Nikhil", "Anjali", "Rohan", "Meera", "Harish", "Shreya"]

LAST_NAMES = ["Kumar", "Singh", "Patel", "Gupta", "Sharma", "Verma", "Reddy", "Iyer", "Nair", "Das"]

CITIES = ["Chennai", "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Kolkata", "Coimbatore"]

# ===== SEED FUNCTIONS =====

def clear_all_collections():
    """Clear all existing data"""
    print("🗑️  Clearing existing collections...")
    collections = [
        'products', 'products_update', 'products_by_user',
        'users', 'users_update', 'workers_update', 'worker_specific_added',
        'products_sold', 'user_data_bought', 'admins', 'labors',
        'chat_history', 'email_logs', 'admin_ai_chats'
    ]
    
    for coll_name in collections:
        try:
            db[coll_name].delete_many({})
            print(f"  ✓ Cleared {coll_name}")
        except Exception as e:
            print(f"  ⚠️  Could not clear {coll_name}: {e}")

def seed_products():
    """Seed products_update collection with realistic products"""
    print("\n📦 Seeding products...")
    
    products_list = []
    for product in TAMIL_PRODUCTS:
        doc = {
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "variants": [
                {
                    "size": "1kg",
                    "stock": product["stock"],
                    "price": product["price"]
                },
                {
                    "size": "500g",
                    "stock": int(product["stock"] * 0.6),
                    "price": int(product["price"] * 0.55)
                }
            ],
            "description": f"High-quality {product['name']} - Fresh and pure",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        products_list.append(doc)
    
    result = db.products_update.insert_many(products_list)
    print(f"  ✓ Created {len(result.inserted_ids)} products")
    return result.inserted_ids

def seed_users():
    """Seed users with realistic data"""
    print("\n👥 Seeding users...")
    
    users_list = []
    user_ids = []
    
    for i in range(50):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"user{i+1}@example.com"
        
        # Varying registration dates (some recent, some older)
        days_ago = random.randint(0, 180)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        user_doc = {
            "name": f"{first_name} {last_name}",
            "email": email,
            "phone": f"98{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(100000000, 999999999):09d}",
            "address": f"{random.randint(1, 500)} {random.choice(['Main St', 'Park Ave', 'Oak Rd', 'Elm St'])}, {random.choice(CITIES)}",
            "city": random.choice(CITIES),
            "created_at": created_at,
            "last_purchase": created_at + timedelta(days=random.randint(1, 50)) if random.random() > 0.3 else created_at,
            "total_spent": 0,
            "purchase_count": 0
        }
        users_list.append(user_doc)
    
    result = db.users.insert_many(users_list)
    user_ids = result.inserted_ids
    print(f"  ✓ Created {len(user_ids)} users")
    return user_ids

def seed_workers():
    """Seed workers"""
    print("\n👷 Seeding workers...")
    
    workers_list = []
    worker_ids = []
    
    for i in range(15):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        worker_doc = {
            "name": f"{first_name} {last_name}",
            "email": f"worker{i+1}@example.com",
            "password": "worker123",
            "phone": f"98{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(100000000, 999999999):09d}",
            "address": f"{random.randint(1, 500)} {random.choice(['Main St', 'Park Ave'])} {random.choice(CITIES)}",
            "role": "worker",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            "last_active": datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
            "sales_today": 0,
            "total_sales": 0
        }
        workers_list.append(worker_doc)
    
    result = db.workers_update.insert_many(workers_list)
    worker_ids = result.inserted_ids
    print(f"  ✓ Created {len(worker_ids)} workers")
    return worker_ids

def seed_admin():
    """Seed admin user"""
    print("\n🔐 Seeding admin...")
    
    admin_doc = {
        "email": "admin",
        "password": "admin123",
        "name": "Admin",
        "role": "admin",
        "created_at": datetime.utcnow()
    }
    
    result = db.admins.insert_one(admin_doc)
    print(f"  ✓ Created admin user")
    return result.inserted_id

def seed_sales_data(user_ids, worker_ids, product_ids):
    """Seed realistic high sales data"""
    print("\n💰 Seeding sales data with high activity...")
    
    sales_count = 0
    total_revenue = 0
    
    # Generate sales for the last 30 days with increasing trend
    for days_back in range(30):
        current_date = datetime.utcnow() - timedelta(days=days_back)
        daily_sales = random.randint(15, 35)  # 15-35 sales per day
        
        for _ in range(daily_sales):
            user_id = random.choice(user_ids)
            worker_id = random.choice(worker_ids)
            product_id = random.choice(product_ids)
            
            # Get product details
            product = db.products_update.find_one({"_id": product_id})
            
            # Random quantity and calculate total
            quantity = random.randint(1, 5)
            variant = random.choice(product.get("variants", []))
            unit_price = variant.get("price", product.get("price", 100))
            
            total = unit_price * quantity
            total_revenue += total
            
            # Insert into user_data_bought (main sales collection)
            sale_doc = {
                "user_id": user_id,
                "sold_by": worker_id,
                "product_id": product_id,
                "product_name": product.get("name", "Unknown"),
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total,
                "category": product.get("category", "Unknown"),
                "purchase_date": current_date,
                "date": current_date,
                "payment_method": random.choice(["Cash", "Card", "UPI", "Online"]),
                "delivery_address": f"Address {random.randint(1, 100)}, {random.choice(CITIES)}",
                "order_status": "Delivered"
            }
            
            db.user_data_bought.insert_one(sale_doc)
            
            # Also insert into products_sold for backward compatibility
            db.products_sold.insert_one(sale_doc)
            
            sales_count += 1
    
    print(f"  ✓ Created {sales_count} sales records")
    print(f"  💵 Total Revenue Simulated: ₹{total_revenue:,.2f}")

def seed_custom_festivals():
    """Seed custom festival discounts"""
    print("\n🎉 Seeding custom festivals...")
    
    festivals = [
        {
            "name": "Holi Celebration",
            "start_date": datetime.utcnow() - timedelta(days=5),
            "end_date": datetime.utcnow() + timedelta(days=10),
            "discount_type": "percentage",
            "discount_value": 20,
            "products": ["சக்கரை (Sugar)", "பால் (Milk)"]
        },
        {
            "name": "Spring Sale",
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=15),
            "discount_type": "percentage",
            "discount_value": 15,
            "products": ["வெண்ணை (Butter)", "பனீர் (Paneer)"]
        },
        {
            "name": "Mega Discount Week",
            "start_date": datetime.utcnow() - timedelta(days=2),
            "end_date": datetime.utcnow() + timedelta(days=5),
            "discount_type": "flat",
            "discount_value": 50,
            "products": ["முந்திரி (Cashew)", "பாதாம் (Almond)"]
        }
    ]
    
    result = db.custom_festivals.insert_many(festivals)
    print(f"  ✓ Created {len(result.inserted_ids)} custom festivals")

def seed_cart_data(user_ids, product_ids):
    """Seed some abandoned carts"""
    print("\n🛒 Seeding cart data...")
    
    for _ in range(10):
        user_id = str(random.choice(user_ids))
        
        cart_items = {}
        for _ in range(random.randint(1, 4)):
            product_id = str(random.choice(product_ids))
            cart_items[product_id] = random.randint(1, 3)
        
        db.carts.insert_one({
            "user_id": user_id,
            "items": cart_items,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    print(f"  ✓ Created sample carts")

def seed_email_logs():
    """Seed email send history"""
    print("\n📧 Seeding email logs...")
    
    email_logs_list = []
    for i in range(50):
        email_log = {
            "to": f"user{random.randint(1, 50)}@example.com",
            "subject": random.choice([
                "Welcome to SalesSense",
                "Your Purchase Confirmation",
                "Festival Offer Available",
                "Restock Notification"
            ]),
            "status": random.choice(["sent", "delivered", "opened"]),
            "sent_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            "type": random.choice(["welcome", "confirmation", "offer", "notification"])
        }
        email_logs_list.append(email_log)
    
    result = db.email_logs.insert_many(email_logs_list)
    print(f"  ✓ Created {len(result.inserted_ids)} email logs")

def print_summary():
    """Print data summary"""
    print("\n" + "="*60)
    print("📊 SAMPLE DATA SUMMARY")
    print("="*60)
    
    collections_stats = {
        "products_update": "Products",
        "users": "Users",
        "workers_update": "Workers",
        "user_data_bought": "Sales Records",
        "products_sold": "Products Sold",
        "custom_festivals": "Custom Festivals",
        "carts": "Shopping Carts",
        "email_logs": "Email Logs",
        "admins": "Admin Accounts"
    }
    
    for coll_name, label in collections_stats.items():
        count = db[coll_name].count_documents({})
        print(f"  • {label}: {count}")
    
    # Calculate total revenue
    total_revenue = db.user_data_bought.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ])
    revenue_result = list(total_revenue)
    if revenue_result:
        total = revenue_result[0].get("total", 0)
        print(f"\n  💰 Total Sales Revenue: ₹{total:,.2f}")
    
    print("\n✅ Seeding completed successfully!")
    print("="*60)

# ===== MAIN EXECUTION =====

def main():
    print("🚀 Starting realistic data seed...")
    print("="*60)
    
    try:
        # Clear existing data
        clear_all_collections()
        
        # Seed all data
        product_ids = seed_products()
        user_ids = seed_users()
        worker_ids = seed_workers()
        seed_admin()
        seed_custom_festivals()
        seed_sales_data(user_ids, worker_ids, product_ids)
        seed_cart_data(user_ids, product_ids)
        seed_email_logs()
        
        # Print summary
        print_summary()
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
