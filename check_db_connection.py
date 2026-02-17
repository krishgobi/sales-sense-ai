from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB connection details
MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

print("="*70)
print("DATABASE CONNECTION CHECK")
print("="*70)
print(f"MongoDB URL: {MONGODB_URL[:80]}...")
print(f"Database Name: {MONGODB_DATABASE}")
print()

# Connect to MongoDB
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]

# Check users collection
users_collection = db['users']
total_users = users_collection.count_documents({})
print(f"✅ Total users in 'users' collection: {total_users}")

# Check users_update collection (maybe it's using the wrong collection?)
users_update_collection = db['users_update']
total_users_update = users_update_collection.count_documents({})
print(f"ℹ️  Total users in 'users_update' collection: {total_users_update}")

# List first 10 users from 'users' collection
print("\n📋 First 10 users from 'users' collection:")
for i, user in enumerate(users_collection.find().limit(10), 1):
    print(f"{i}. {user.get('name', 'N/A')} - {user.get('email', 'N/A')}")

print("\n📋 First 10 users from 'users_update' collection:")
for i, user in enumerate(users_update_collection.find().limit(10), 1):
    print(f"{i}. {user.get('name', 'N/A')} - {user.get('email', 'N/A')}")

print("\n" + "="*70)
