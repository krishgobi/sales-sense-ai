from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

print("="*60)
print("DATABASE USER COUNT CHECK")
print("="*60)

total_users = db.users.count_documents({})
print(f"\nTotal users in database: {total_users}")

active_users = db.users.count_documents({'is_active': True})
print(f"Active users: {active_users}")

print("\nFirst 10 users:")
for i, user in enumerate(db.users.find().limit(10), 1):
    print(f"{i}. {user.get('name')}: {user.get('email')}")

print("\n" + "="*60)
