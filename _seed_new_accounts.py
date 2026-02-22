"""Create 2 new workers and 2 new labour (customer) accounts in MongoDB."""
from dotenv import load_dotenv; load_dotenv()
import os, datetime
from pymongo import MongoClient

db = MongoClient(os.getenv('MONGODB_URL'))[os.getenv('MONGODB_DATABASE', 'saless')]

now = datetime.datetime.now()

# ── New Workers ─────────────────────────────────────────────────────────────
new_workers = [
    {
        'name': 'Priya Lakshmi',
        'email': 'priya.worker@salessense.com',
        'password': 'Priya@2026',
        'phone': '9876543210',
        'role': 'Worker',
        'status': 'Active',
        'date_of_joining': now,
        'created_at': now,
        'last_active': None,
        'total_products_added': 0,
        'total_revenue': 0.0,
        'total_sales': 0,
    },
    {
        'name': 'Arjun Selvam',
        'email': 'arjun.worker@salessense.com',
        'password': 'Arjun@2026',
        'phone': '9123456780',
        'role': 'Worker',
        'status': 'Active',
        'date_of_joining': now,
        'created_at': now,
        'last_active': None,
        'total_products_added': 0,
        'total_revenue': 0.0,
        'total_sales': 0,
    },
]

# ── New Labour/Customers ─────────────────────────────────────────────────────
new_users = [
    {
        'name': 'Meena Rajendran',
        'email': 'meena.customer@salessense.com',
        'mobile': '9988776655',
        'phone': '9988776655',
        'created_at': now,
        'join_date': now,
        'loyalty_points': 0,
        'total_purchases': 0,
    },
    {
        'name': 'Karthik Venkat',
        'email': 'karthik.customer@salessense.com',
        'mobile': '9112233445',
        'phone': '9112233445',
        'created_at': now,
        'join_date': now,
        'loyalty_points': 0,
        'total_purchases': 0,
    },
]

# Insert workers
workers_col = db['workers_update']
print("=== Inserting Workers ===")
for w in new_workers:
    existing = workers_col.find_one({'email': w['email']})
    if existing:
        print(f"  Already exists: {w['email']}")
    else:
        result = workers_col.insert_one(w)
        print(f"  ✅ Inserted: {w['name']} | {w['email']} | {w['password']} (id={result.inserted_id})")

# Insert labour into BOTH users and users_update so admin dashboard and labour login both work
print("\n=== Inserting Labour/Customers ===")
for u in new_users:
    for col_name in ['users', 'users_update']:
        col = db[col_name]
        existing = col.find_one({'email': u['email']})
        if existing:
            print(f"  Already exists in {col_name}: {u['email']}")
        else:
            result = col.insert_one(dict(u))  # dict() to avoid same _id across inserts
            print(f"  ✅ Inserted into {col_name}: {u['name']} | {u['email']} | mobile: {u['mobile']}")

print("\n=== Done ===")
print("\nNew Worker credentials:")
for w in new_workers:
    print(f"  Name: {w['name']}")
    print(f"  Email: {w['email']}")
    print(f"  Password: {w['password']}")
    print()

print("New Labour credentials (login with email OR mobile — no password):")
for u in new_users:
    print(f"  Name: {u['name']}")
    print(f"  Email: {u['email']}")
    print(f"  Mobile: {u['mobile']}")
    print()
