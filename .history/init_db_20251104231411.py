from pymongo import MongoClient
import os
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

# Sample products
products = [
    # Groceries
    {"name": "Rice - Premium Quality", "category": "Groceries", "price": 15.99, "stock": 100},
    {"name": "Wheat Flour", "category": "Groceries", "price": 5.99, "stock": 150},
    {"name": "Sugar", "category": "Groceries", "price": 4.99, "stock": 200},
    {"name": "Salt", "category": "Groceries", "price": 1.99, "stock": 300},
    
    # Beverages
    {"name": "Cola - 2L", "category": "Beverages", "price": 2.99, "stock": 100},
    {"name": "Orange Juice - 1L", "category": "Beverages", "price": 3.99, "stock": 80},
    {"name": "Mineral Water - 1L", "category": "Beverages", "price": 1.49, "stock": 200},
    
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

# Insert products into database
try:
    # Clear existing products
    db.products.delete_many({})
    
    # Insert new products
    result = db.products.insert_many(products)
    print(f"Successfully inserted {len(result.inserted_ids)} products")
except Exception as e:
    print(f"An error occurred: {e}")

# Close the connection
client.close()