"""
Check which database and show exact user data that should appear on dashboard
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

print(f"\n{'='*70}")
print(f"DATABASE CONNECTION CHECK")
print(f"{'='*70}")
print(f"MongoDB URL: {MONGODB_URL}")
print(f"Database Name: {MONGODB_DATABASE}")

client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]

# List all collections
print(f"\n📦 Collections in database:")
for coll in db.list_collection_names():
    count = db[coll].count_documents({})
    print(f"  - {coll}: {count} documents")

# Check users collection
users = db['users']
total = users.count_documents({})

print(f"\n👥 USERS COLLECTION:")
print(f"Total users: {total}")

print(f"\n📋 First 20 users (what should show on page 1):")
for i, user in enumerate(users.find().sort('created_at', -1).limit(20), 1):
    join_date = user.get('join_date', 'N/A')
    if hasattr(join_date, 'strftime'):
        join_date = join_date.strftime('%Y-%m-%d')
    print(f"{i}. {user.get('name'):30} | {user.get('email'):35} | {join_date}")

# Check if those 4 specific users exist
print(f"\n🔍 Checking for the 4 users shown in your screenshot:")
test_emails = [
    'gobibhuvi1415@gmail.com',
    'krishgobish@gmail.com', 
    'gobikrish1408@gmail.com',
    'subhashreenatraj@gmail.com'
]

for email in test_emails:
    user = users.find_one({'email': email})
    if user:
        print(f"  ✅ Found: {user.get('name')} - {email}")
    else:
        print(f"  ❌ Not found: {email}")

print(f"\n{'='*70}\n")

client.close()
