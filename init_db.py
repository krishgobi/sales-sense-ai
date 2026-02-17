from pymongo import MongoClient
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

# Sample product categories
categories = [
    "மளிகை (Groceries)",
    "பானங்கள் (Beverages)",
    "தின்பண்டங்கள் (Snacks)",
    "பால் பொருட்கள் (Dairy)",
    "காய்கறிகள் & பழங்கள் (Vegetables & Fruits)",
    "தனிப்பட்ட பராமரிப்பு (Personal Care)",
    "வீட்டுப் பொருட்கள் (Household)",
    "பேக்கரி (Bakery)"
]

# Sample products with variants - All Tamil/Indian products
products = [
    # மளிகை (Groceries)
    {
        "name": "பாசுமதி அரிசி (Basmati Rice)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "1kg", "price": 120.00, "stock": 100},
            {"quantity": "5kg", "price": 580.00, "stock": 50},
            {"quantity": "10kg", "price": 1150.00, "stock": 25}
        ]
    },
    {
        "name": "இட்லி அரிசி (Idli Rice)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "1kg", "price": 85.00, "stock": 150},
            {"quantity": "5kg", "price": 410.00, "stock": 100},
            {"quantity": "10kg", "price": 800.00, "stock": 75}
        ]
    },
    {
        "name": "கோதுமை மாவு (Wheat Flour)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "500g", "price": 35.00, "stock": 150},
            {"quantity": "1kg", "price": 65.00, "stock": 100},
            {"quantity": "2kg", "price": 125.00, "stock": 75}
        ]
    },
    {
        "name": "பருப்பு - துவரம் (Toor Dal)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "500g", "price": 75.00, "stock": 120},
            {"quantity": "1kg", "price": 145.00, "stock": 80},
            {"quantity": "2kg", "price": 280.00, "stock": 40}
        ]
    },
    {
        "name": "தேங்காய் எண்ணெய் (Coconut Oil)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "500ml", "price": 180.00, "stock": 90},
            {"quantity": "1L", "price": 340.00, "stock": 60},
            {"quantity": "2L", "price": 650.00, "stock": 30}
        ]
    },
    {
        "name": "சாம்பார் பொடி (Sambar Powder)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "100g", "price": 45.00, "stock": 150},
            {"quantity": "250g", "price": 105.00, "stock": 100},
            {"quantity": "500g", "price": 195.00, "stock": 60}
        ]
    },
    {
        "name": "ரசம் பொடி (Rasam Powder)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "100g", "price": 40.00, "stock": 140},
            {"quantity": "250g", "price": 95.00, "stock": 90},
            {"quantity": "500g", "price": 180.00, "stock": 50}
        ]
    },
    {
        "name": "வெல்லம் (Jaggery)",
        "category": "மளிகை (Groceries)",
        "variants": [
            {"quantity": "500g", "price": 65.00, "stock": 110},
            {"quantity": "1kg", "price": 125.00, "stock": 70},
            {"quantity": "2kg", "price": 240.00, "stock": 35}
        ]
    },
    
    # பானங்கள் (Beverages)
    {
        "name": "பால் (Milk)",
        "category": "பானங்கள் (Beverages)",
        "variants": [
            {"quantity": "500ml", "price": 28.00, "stock": 200},
            {"quantity": "1L", "price": 54.00, "stock": 150},
            {"quantity": "2L", "price": 105.00, "stock": 100}
        ]
    },
    {
        "name": "தயிர் (Curd/Yogurt)",
        "category": "பானங்கள் (Beverages)",
        "variants": [
            {"quantity": "200g", "price": 25.00, "stock": 180},
            {"quantity": "400g", "price": 48.00, "stock": 120},
            {"quantity": "1kg", "price": 110.00, "stock": 80}
        ]
    },
    {
        "name": "பட்டர்மில்க் (Buttermilk)",
        "category": "பானங்கள் (Beverages)",
        "variants": [
            {"quantity": "500ml", "price": 20.00, "stock": 150},
            {"quantity": "1L", "price": 38.00, "stock": 100}
        ]
    },
    {
        "name": "வடாம் (Papad/Appalam)",
        "category": "தின்பண்டங்கள் (Snacks)",
        "variants": [
            {"quantity": "100g", "price": 35.00, "stock": 120},
            {"quantity": "200g", "price": 65.00, "stock": 80},
            {"quantity": "500g", "price": 155.00, "stock": 40}
        ]
    },
    {
        "name": "முறுக்கு (Murukku)",
        "category": "தின்பண்டங்கள் (Snacks)",
        "variants": [
            {"quantity": "100g", "price": 45.00, "stock": 100},
            {"quantity": "250g", "price": 105.00, "stock": 70},
            {"quantity": "500g", "price": 195.00, "stock": 40}
        ]
    },
    {
        "name": "மிக்சர் (Mixture)",
        "category": "தின்பண்டங்கள் (Snacks)",
        "variants": [
            {"quantity": "100g", "price": 40.00, "stock": 110},
            {"quantity": "250g", "price": 95.00, "stock": 75},
            {"quantity": "500g", "price": 180.00, "stock": 45}
        ]
    }
]

# Add more sample products programmatically
def generate_more_products():
    additional_products = []
    
    # மளிகை (Groceries)
    groceries = [
        ("மஞ்சள் பொடி (Turmeric Powder)", 85.00),
        ("மிளகாய் பொடி (Chilli Powder)", 95.00),
        ("கொத்தமல்லி பொடி (Coriander Powder)", 75.00),
        ("சீரகம் (Cumin Seeds)", 180.00),
        ("ஏலக்காய் (Cardamom)", 850.00),
        ("புளி (Tamarind)", 65.00),
        ("கடுகு (Mustard Seeds)", 95.00),
        ("மிளகு (Black Pepper)", 420.00),
        ("தேங்காய் துருவல் (Coconut Powder)", 125.00),
        ("உப்பு (Salt)", 25.00)
    ]
    
    for name, price in groceries:
        additional_products.append({
            "name": name,
            "category": "மளிகை (Groceries)",
            "variants": [
                {"quantity": "100g", "price": price * 0.4, "stock": 100 + (hash(name) % 100)},
                {"quantity": "250g", "price": price, "stock": 80 + (hash(name) % 80)},
                {"quantity": "500g", "price": price * 1.9, "stock": 50 + (hash(name) % 50)}
            ]
        })
    
    # தின்பண்டங்கள் (Snacks)
    snacks = [
        ("சீடை (Seedai)", 95.00),
        ("லட்டு (Laddu)", 180.00),
        ("ஜாங்கிரி (Jangri)", 220.00),
        ("அதிரசம் (Adhirasam)", 165.00),
        ("தட்டை (Thattai)", 75.00),
        ("கடலை மிட்டாய் (Peanut Candy)", 85.00)
    ]
    
    for name, price in snacks:
        additional_products.append({
            "name": name,
            "category": "தின்பண்டங்கள் (Snacks)",
            "variants": [
                {"quantity": "100g", "price": price * 0.5, "stock": 50 + (hash(name) % 100)},
                {"quantity": "250g", "price": price, "stock": 40 + (hash(name) % 80)},
                {"quantity": "500g", "price": price * 1.85, "stock": 25 + (hash(name) % 50)}
            ]
        })
    
    # காய்கறிகள் (Vegetables)
    vegetables = [
        ("உருளைக்கிழங்கு (Potato)", 35.00),
        ("தக்காளி (Tomato)", 28.00),
        ("வெங்காயம் (Onion)", 32.00),
        ("பூண்டு (Garlic)", 125.00),
        ("பச்சை மிளகாய் (Green Chilli)", 45.00),
        ("கேரட் (Carrot)", 42.00)
    ]
    
    for name, price in vegetables:
        additional_products.append({
            "name": name,
            "category": "காய்கறிகள் & பழங்கள் (Vegetables & Fruits)",
            "variants": [
                {"quantity": "500g", "price": price, "stock": 150 + (hash(name) % 100)},
                {"quantity": "1kg", "price": price * 1.8, "stock": 100 + (hash(name) % 80)}
            ]
        })
    
    # தனிப்பட்ட பராமரிப்பு (Personal Care)
    personal_care = [
        ("சீயக்காய் பொடி (Shikakai Powder)", 95.00),
        ("நெல்லிக்காய் பொடி (Amla Powder)", 110.00),
        ("சந்தனம் (Sandalwood)", 580.00),
        ("வேப்பிலை சோப்பு (Neem Soap)", 45.00),
        ("தேங்காய் எண்ணெய் - தலைக்கு (Coconut Hair Oil)", 125.00)
    ]
    
    for name, price in personal_care:
        additional_products.append({
            "name": name,
            "category": "தனிப்பட்ட பராமரிப்பு (Personal Care)",
            "variants": [
                {"quantity": "100g/100ml", "price": price, "stock": 80 + (hash(name) % 70)},
                {"quantity": "200g/200ml", "price": price * 1.85, "stock": 60 + (hash(name) % 50)}
            ]
        })
    
    return additional_products

# Add the additional products
products.extend(generate_more_products())

# Admin credentials
admin = {
    "email": "admin@salessense.com",
    "password": "admin123",  # In production, use hashed password
    "name": "Admin",
    "role": "admin",
    "created_at": datetime.datetime.utcnow()
}

# Insert products into database
try:
    # Clear existing products and admin collections
    db.products_update.delete_many({})
    db.admins.delete_many({})
    
    # Insert admin user
    db.admins.insert_one(admin)
    print(f"Successfully created admin user: {admin['email']}")
    
    # Insert new products
    result = db.products_update.insert_many(products)
    print(f"Successfully inserted {len(result.inserted_ids)} products")

    # Create indexes for products collections
    db.products_update.create_index("name")
    db.products_update.create_index("category")
    
    # Create indexes for sales tracking collections
    db.products_sold.create_index("product_id")
    db.products_sold.create_index("date")
    db.products_by_user.create_index("user_id")
    db.products_by_user.create_index([("user_id", 1), ("date", -1)])
    
    # Create indexes for worker collections
    db.workers_update.create_index("email", unique=True)
    db.worker_specific_added.create_index("worker_id")
    db.worker_specific_added.create_index([("worker_id", 1), ("date", -1)])

except Exception as e:
    print(f"An error occurred: {e}")

# Close the connection
client.close()