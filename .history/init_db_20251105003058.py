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
    "Groceries",
    "Beverages",
    "Snacks",
    "Dairy",
    "Fruits & Vegetables",
    "Personal Care",
    "Household",
    "Bakery"
]

# Sample products with variants
products = [
    # Groceries
    {
        "name": "Rice - Premium Quality",
        "category": "Groceries",
        "variants": [
            {"quantity": "1kg", "price": 15.99, "stock": 100},
            {"quantity": "5kg", "price": 75.99, "stock": 50},
            {"quantity": "10kg", "price": 145.99, "stock": 25}
        ]
    },
    {
        "name": "Wheat Flour",
        "category": "Groceries",
        "variants": [
            {"quantity": "500g", "price": 3.99, "stock": 150},
            {"quantity": "1kg", "price": 5.99, "stock": 100},
            {"quantity": "2kg", "price": 10.99, "stock": 75}
        ]
    },
    {
        "name": "Cola",
        "category": "Beverages",
        "variants": [
            {"quantity": "500ml", "price": 1.99, "stock": 200},
            {"quantity": "1L", "price": 2.99, "stock": 150},
            {"quantity": "2L", "price": 4.99, "stock": 100}
        ]
    },
    
    # Add more products for each category...
]

# Add more sample products programmatically
def generate_more_products():
    additional_products = []
    
    # Groceries
    groceries = [
        ("Pasta", 2.99), ("Cooking Oil", 8.99), ("Lentils", 3.99),
        ("Beans", 2.99), ("Chickpeas", 2.49), ("Tomato Sauce", 1.99)
    ]
    
    for name, price in groceries:
        additional_products.append({
            "name": name,
            "category": "Groceries",
            "price": price,
            "stock": 100 + (hash(name) % 100)  # Random stock between 100-199
        })
    
    # Snacks
    snacks = [
        ("Potato Chips", 3.99), ("Popcorn", 2.99), ("Pretzels", 2.49),
        ("Chocolate Bar", 1.99), ("Cookies", 3.49), ("Nuts Mix", 5.99)
    ]
    
    for name, price in snacks:
        additional_products.append({
            "name": name,
            "category": "Snacks",
            "price": price,
            "stock": 50 + (hash(name) % 100)  # Random stock between 50-149
        })
    
    # Add more categories...
    
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