"""
seed_daily_sales.py
-------------------
Generates realistic daily sales data in user_data_bought for every day
from START_DATE to today (or a specified end date).

Usage:
    python seed_daily_sales.py                 # last 60 days, 8-20 sales/day
    python seed_daily_sales.py --days 30       # last 30 days
    python seed_daily_sales.py --start 2025-01-01 --end 2025-06-30
    python seed_daily_sales.py --per-day 15    # fixed 15 sales per day
    python seed_daily_sales.py --clear         # WIPE seeded docs, then re-seed
"""

import argparse
import datetime
import random
import string
import os
import sys

# ── MongoDB connection ──────────────────────────────────────────────────────
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run:  pip install pymongo python-dotenv")
    sys.exit(1)

load_dotenv()
MONGO_URI = (os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or
             os.getenv('MONGO_URL') or os.getenv('MONGODB_URL'))
if not MONGO_URI:
    print("ERROR: Set MONGO_URI (or MONGODB_URL) in your .env file.")
    sys.exit(1)

client = MongoClient(MONGO_URI)

# Auto-detect database name
db_name = (os.getenv('MONGODB_DATABASE') or
           MONGO_URI.split('/')[-1].split('?')[0] or 'sales_db')
db = client[db_name]

# ── Static Tamil product catalogue (fallback if DB empty) ────────────────────
FALLBACK_PRODUCTS = [
    {"name": "பாசுமதி அரிசி",       "category": "அரிசி வகைகள்",       "price": 120},
    {"name": "சீரக சம்பா அரிசி",    "category": "அரிசி வகைகள்",       "price": 95},
    {"name": "ஆட்டா மாவு",          "category": "மாவு வகைகள்",        "price": 55},
    {"name": "கோதுமை மாவு",         "category": "மாவு வகைகள்",        "price": 48},
    {"name": "தூய நெய்",            "category": "கொழுப்பு வகைகள்",   "price": 450},
    {"name": "கடலை எண்ணெய்",       "category": "கொழுப்பு வகைகள்",   "price": 180},
    {"name": "துவரம் பருப்பு",       "category": "பருப்பு வகைகள்",    "price": 110},
    {"name": "கடலை பருப்பு",        "category": "பருப்பு வகைகள்",    "price": 90},
    {"name": "சர்க்கரை",            "category": "இனிப்பு வகைகள்",   "price": 42},
    {"name": "வெல்லம்",             "category": "இனிப்பு வகைகள்",   "price": 60},
    {"name": "சாம்பார் பொடி",       "category": "மசாலா வகைகள்",     "price": 35},
    {"name": "மிளகாய் தூள்",        "category": "மசாலா வகைகள்",     "price": 30},
    {"name": "மஞ்சள் தூள்",         "category": "மசாலா வகைகள்",     "price": 25},
    {"name": "தக்காளி கெட்சப்",     "category": "சாஸ் வகைகள்",      "price": 55},
    {"name": "பாதாம்",              "category": "கொட்டை வகைகள்",    "price": 350},
    {"name": "முந்திரி",            "category": "கொட்டை வகைகள்",    "price": 400},
    {"name": "பால் பொடி",           "category": "பால் வகைகள்",       "price": 220},
    {"name": "தேன்",                "category": "இயற்கை வகைகள்",   "price": 185},
    {"name": "கடுகு",               "category": "மசாலா வகைகள்",     "price": 20},
    {"name": "இஞ்சி-பூண்டு விழுது", "category": "மசாலா வகைகள்",     "price": 45},
]

VARIANTS = ["500g", "1kg", "2kg", "5kg", "250g", "200ml", "500ml", "1L"]
PAYMENT_STATUSES = ["completed", "completed", "completed", "pending"]
WORKER_NAMES = ["Gobi", "Bhuvaneswari", "Anandha", "Karthi", "Priya", "Selva"]


def load_products():
    """Load products from DB collections; fall back to static list."""
    products = []
    for col in ['products_update', 'products', 'products_by_user']:
        for p in db[col].find({}, {'name': 1, 'category': 1, 'price': 1, 'variants': 1}):
            if not p.get('name'):
                continue
            # Determine price
            price = None
            if p.get('variants') and isinstance(p['variants'], list) and p['variants']:
                price = p['variants'][0].get('price')
            if not price:
                price = p.get('price') or random.randint(30, 500)
            products.append({
                'name': p['name'],
                'category': p.get('category', 'பொது வகை'),
                'price': float(price)
            })
    if not products:
        print("  ⚠  No products in DB – using built-in catalogue.")
        products = [p.copy() for p in FALLBACK_PRODUCTS]
    return products


def load_users():
    """Load users from DB; generate fake users if empty."""
    users = []
    for col in ['users_update', 'users']:
        for u in db[col].find({}, {'name': 1, 'email': 1, '_id': 1}):
            users.append({
                'id': str(u.get('_id', '')),
                'name': u.get('name', 'Customer'),
                'email': u.get('email', 'user@example.com')
            })
    if not users:
        print("  ⚠  No users in DB – generating fake users.")
        NAMES = ["அரவிந்த்", "கவிதா", "மோகன்", "சரண்யா", "விக்ரம்",
                 "அனிதா", "பரத்", "லட்சுமி", "கோபி", "தீப்திகா"]
        for i, n in enumerate(NAMES):
            users.append({'id': f'fake_{i}', 'name': n, 'email': f'user{i}@example.com'})
    return users


def random_time_on_day(day: datetime.date) -> datetime.datetime:
    """Random datetime within business hours (8am-9pm) on a given date."""
    hour = random.randint(8, 20)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime.datetime(day.year, day.month, day.day, hour, minute, second)


def build_records(day: datetime.date, products, users, count: int) -> list:
    records = []
    worker_name = random.choice(WORKER_NAMES)
    worker_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    for _ in range(count):
        product = random.choice(products)
        user = random.choice(users)
        quantity = random.randint(1, 3)
        unit_price = round(product['price'] * random.uniform(0.9, 1.1), 2)
        total = round(unit_price * quantity, 2)
        records.append({
            'user_id': user['id'],
            'user_name': user['name'],
            'user_email': user['email'],
            'product_name': product['name'],
            'category': product['category'],
            'variant': random.choice(VARIANTS),
            'quantity': quantity,
            'price': unit_price,
            'total': total,
            'sold_by': worker_id,
            'sold_by_name': worker_name,
            'purchase_date': random_time_on_day(day),
            'payment_status': random.choice(PAYMENT_STATUSES),
            '_seeded': True  # marker so we can clear easily
        })
    return records


def seed(start: datetime.date, end: datetime.date, per_day_min: int, per_day_max: int):
    products = load_products()
    users = load_users()
    print(f"  Loaded {len(products)} products and {len(users)} users from DB.\n")

    collection = db['user_data_bought']
    current = start
    total_inserted = 0

    while current <= end:
        count = per_day_min if per_day_min == per_day_max else random.randint(per_day_min, per_day_max)
        records = build_records(current, products, users, count)
        collection.insert_many(records)
        total_inserted += len(records)
        print(f"  ✅  {current.strftime('%Y-%m-%d')}  →  {len(records)} sales inserted")
        current += datetime.timedelta(days=1)

    print(f"\n🎉  Done! Inserted {total_inserted} sales records across {(end - start).days + 1} days.")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed daily sales data into user_data_bought')
    parser.add_argument('--days', type=int, default=60,
                        help='Number of past days to seed (default: 60)')
    parser.add_argument('--start', type=str, default=None,
                        help='Start date YYYY-MM-DD (overrides --days)')
    parser.add_argument('--end', type=str, default=None,
                        help='End date YYYY-MM-DD (default: today)')
    parser.add_argument('--per-day', type=int, default=None,
                        help='Fixed number of sales per day (e.g. 15)')
    parser.add_argument('--min-per-day', type=int, default=8,
                        help='Minimum random sales per day (default: 8)')
    parser.add_argument('--max-per-day', type=int, default=20,
                        help='Maximum random sales per day (default: 20)')
    parser.add_argument('--clear', action='store_true',
                        help='Delete previously seeded records (_seeded=True) before inserting')
    args = parser.parse_args()

    today = datetime.date.today()

    end_date = datetime.date.fromisoformat(args.end) if args.end else today
    if args.start:
        start_date = datetime.date.fromisoformat(args.start)
    else:
        start_date = end_date - datetime.timedelta(days=args.days - 1)

    per_min = args.per_day if args.per_day else args.min_per_day
    per_max = args.per_day if args.per_day else args.max_per_day

    if args.clear:
        deleted = db['user_data_bought'].delete_many({'_seeded': True})
        print(f"🗑  Cleared {deleted.deleted_count} previously seeded records.\n")

    print(f"📅  Seeding sales from {start_date} to {end_date} ({(end_date-start_date).days+1} days)")
    print(f"📊  {per_min}–{per_max} sales per day\n")
    seed(start_date, end_date, per_min, per_max)
