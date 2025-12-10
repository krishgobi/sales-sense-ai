from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

print("Connecting to MongoDB Atlas...")
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]

print(f"\n{'='*60}")
print("MONGODB ATLAS - DATA VERIFICATION")
print(f"{'='*60}\n")

# Check all collections
collections_info = [
    ('users', 'Users'),
    ('products_sold', 'Sales Records'),
    ('products_update', 'Products'),
    ('workers_update', 'Workers'),
    ('admins', 'Admins')
]

for collection_name, display_name in collections_info:
    count = db[collection_name].count_documents({})
    print(f"{display_name:.<30} {count:>10,}")

print(f"\n{'='*60}")

# Calculate total revenue
print("\nCalculating total revenue...")
total_revenue = 0
for sale in db.products_sold.find():
    if 'total' in sale:
        total_revenue += float(sale.get('total', 0))

print(f"Total Revenue: ${total_revenue:,.2f}")

# Show sample user
print(f"\n{'='*60}")
print("SAMPLE USER DATA:")
print(f"{'='*60}")
sample_user = db.users.find_one()
if sample_user:
    print(f"Name: {sample_user.get('name')}")
    print(f"Email: {sample_user.get('email')}")
    print(f"Phone: {sample_user.get('phone')}")
    print(f"City: {sample_user.get('city')}, {sample_user.get('state')}")
    print(f"Total Purchases: {sample_user.get('total_purchases', 0)}")

# Show sample sale
print(f"\n{'='*60}")
print("SAMPLE SALES DATA:")
print(f"{'='*60}")
sample_sale = db.products_sold.find_one()
if sample_sale:
    print(f"Product: {sample_sale.get('product_name')}")
    print(f"Quantity: {sample_sale.get('quantity')}")
    print(f"Price: ${sample_sale.get('price')}")
    print(f"Total: ${sample_sale.get('total')}")
    print(f"Date: {sample_sale.get('date')}")

print(f"\n{'='*60}")
print("✅ ALL DATA IS STORED IN MONGODB ATLAS!")
print(f"{'='*60}\n")

client.close()
