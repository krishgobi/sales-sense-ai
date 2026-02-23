from dotenv import load_dotenv; load_dotenv()
import os
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI') or os.getenv('MONGO_URI'))
db = client['saless']

print("=== workers_update (raw) ===")
for w in db['workers_update'].find().limit(10):
    print({k: v for k, v in w.items() if k != '_id'})

print("\n=== Workers (raw) ===")
for w in db['Workers'].find().limit(10):
    print({k: v for k, v in w.items() if k != '_id'})

print("\n=== workers (raw) ===")
for w in db['workers'].find().limit(10):
    print({k: v for k, v in w.items() if k != '_id'})

print("\n=== users_update (raw) ===")
for u in db['users_update'].find().limit(5):
    print({k: v for k, v in u.items() if k != '_id'})

print("\n=== users (first 3) ===")
for u in db['users'].find().limit(3):
    print({k: v for k, v in u.items() if k != '_id'})
