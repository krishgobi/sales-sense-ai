"""
seed_sales_data.py
──────────────────
Inserts realistic Indian-market sales data into MongoDB so that the
Sales Sense AI analytics dashboard shows meaningful numbers:

  • Total revenue  > ₹50,000  (targets ~₹1.2 L across all time)
  • Last 77 days   → solid data spread  (2–8 orders/day)
  • Last 30 days   → slightly richer    (3–10 orders/day)
  • Today          → 6–12 orders        (strong today-stats)
  • Products sold, top-products, category breakdown all populated

Collections written:
  user_data_bought  – one row per line-item (what /api/business-stats reads)
  products_sold     – one row per transaction (for total_orders count)

Run:
    python seed_sales_data.py
"""

import datetime
import random
import os
import sys
from dotenv import load_dotenv
import pymongo

# ──────────────────────────────────────────────
# Load config from .env exactly like app.py does
# ──────────────────────────────────────────────
load_dotenv()

MONGODB_URL      = os.getenv("MONGODB_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "saless")

if not MONGODB_URL:
    print("[ERROR] MONGODB_URL not found in .env")
    sys.exit(1)

print(f"[INFO] Connecting to MongoDB…")
client = pymongo.MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
client.admin.command("ping")
print("[OK]   Connected!")

db                = client[MONGODB_DATABASE]
user_data_bought  = db["user_data_bought"]
products_sold_col = db["products_sold"]

# ──────────────────────────────────────────────
# Seed data: products and customers
# ──────────────────────────────────────────────
PRODUCTS = [
    {"name": "Tata Salt 1kg",          "category": "Groceries",    "variants": [{"label": "1 kg",  "price": 22}]},
    {"name": "Fortune Sunflower Oil",  "category": "Groceries",    "variants": [{"label": "1 L",   "price": 135}, {"label": "5 L", "price": 640}]},
    {"name": "Aashirvaad Atta 5kg",    "category": "Groceries",    "variants": [{"label": "5 kg",  "price": 260}]},
    {"name": "Amul Butter 500g",       "category": "Dairy",        "variants": [{"label": "500 g", "price": 275}]},
    {"name": "Amul Full Cream Milk",   "category": "Dairy",        "variants": [{"label": "500 ml","price": 30},  {"label": "1 L", "price": 62}]},
    {"name": "Parle-G Biscuits",       "category": "Snacks",       "variants": [{"label": "800 g", "price": 95}]},
    {"name": "Lay's Classic Salted",   "category": "Snacks",       "variants": [{"label": "26 g",  "price": 20},  {"label": "73 g","price": 55}]},
    {"name": "Maggi Noodles",          "category": "Instant Food", "variants": [{"label": "2-pack","price": 28},  {"label": "12-pack","price": 165}]},
    {"name": "Dettol Soap",            "category": "Personal Care","variants": [{"label": "75 g",  "price": 38},  {"label": "125 g","price": 58}]},
    {"name": "Colgate MaxFresh",       "category": "Personal Care","variants": [{"label": "150 g", "price": 105}, {"label": "300 g","price": 190}]},
    {"name": "Clinic Plus Shampoo",    "category": "Personal Care","variants": [{"label": "175 ml","price": 110}]},
    {"name": "Surf Excel Detergent",   "category": "Household",    "variants": [{"label": "1 kg",  "price": 235}, {"label": "3 kg","price": 680}]},
    {"name": "Harpic Power Plus",      "category": "Household",    "variants": [{"label": "500 ml","price": 120}]},
    {"name": "Vim Bar",                "category": "Household",    "variants": [{"label": "200 g", "price": 30}]},
    {"name": "Haldiram Bhujia 400g",   "category": "Snacks",       "variants": [{"label": "400 g", "price": 180}]},
    {"name": "Britannia Good Day",     "category": "Snacks",       "variants": [{"label": "200 g", "price": 42}]},
    {"name": "Saffola Gold Oil",       "category": "Groceries",    "variants": [{"label": "1 L",   "price": 195}, {"label": "5 L","price": 930}]},
    {"name": "Red Label Tea 500g",     "category": "Beverages",    "variants": [{"label": "500 g", "price": 240}]},
    {"name": "Bru Instant Coffee",     "category": "Beverages",    "variants": [{"label": "100 g", "price": 155}]},
    {"name": "Pepsi 2L",               "category": "Beverages",    "variants": [{"label": "2 L",   "price": 95}]},
    {"name": "Lipton Green Tea",       "category": "Beverages",    "variants": [{"label": "25 bags","price": 145}]},
    {"name": "Munch Chocolate",        "category": "Snacks",       "variants": [{"label": "13 g",  "price": 10},  {"label": "50 g","price": 40}]},
    {"name": "Glucose D Powder",       "category": "Beverages",    "variants": [{"label": "500 g", "price": 130}]},
    {"name": "Himalaya Face Wash",     "category": "Personal Care","variants": [{"label": "100 ml","price": 115}]},
    {"name": "Dove Soap",              "category": "Personal Care","variants": [{"label": "100 g", "price": 75}]},
]

CUSTOMERS = [
    ("Aravind Kumar",    "aravind.k@gmail.com"),
    ("Priya Suresh",     "priya.s@yahoo.com"),
    ("Karthik Raj",      "karthik.raj@gmail.com"),
    ("Meena Lakshmi",    "meena.l@hotmail.com"),
    ("Suresh Pandian",   "suresh.p@gmail.com"),
    ("Deepa Natarajan",  "deepa.n@gmail.com"),
    ("Vijay Murugan",    "vijay.m@yahoo.com"),
    ("Kavitha Arun",     "kavitha.a@gmail.com"),
    ("Ramesh Babu",      "ramesh.b@gmail.com"),
    ("Anitha Selvam",    "anitha.s@hotmail.com"),
    ("Senthil Kumar",    "senthil.k@gmail.com"),
    ("Lakshmi Priya",    "lakshmi.p@gmail.com"),
    ("Balaji Rajan",     "balaji.r@yahoo.com"),
    ("Saranya Devi",     "saranya.d@gmail.com"),
    ("Murugan Pillai",   "murugan.p@gmail.com"),
    ("Nithya Ramaswamy", "nithya.r@gmail.com"),
    ("Govindaraj S",     "govind.s@gmail.com"),
    ("Sangeetha V",      "sangeetha.v@yahoo.com"),
    ("Prakash M",        "prakash.m@gmail.com"),
    ("Divya R",          "divya.r@gmail.com"),
]

WORKERS = [
    ("w001", "Ravi Kumar"),
    ("w002", "Mani Selvan"),
    ("w003", "Thamizh Selvi"),
]

random.seed(42)          # reproducible run

def random_time(base_date: datetime.datetime) -> datetime.datetime:
    """Returns base_date + random hour/minute/second within a business day."""
    h = random.randint(8, 20)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return base_date.replace(hour=h, minute=m, second=s, microsecond=0)

def pick_product():
    p = random.choice(PRODUCTS)
    v = random.choice(p["variants"])
    qty = random.randint(1, 5)
    return p["name"], p["category"], v["label"], float(v["price"]), qty

def build_transaction(ts: datetime.datetime):
    """Build one transaction with 1–5 line-items."""
    n_items = random.randint(1, 5)
    customer = random.choice(CUSTOMERS)
    worker   = random.choice(WORKERS)
    customer_id   = f"cust_{customer[0].replace(' ','_').lower()}"
    worker_id, worker_name = worker

    line_items   = []
    purchase_recs = []
    total_amount = 0.0

    for _ in range(n_items):
        pname, cat, variant_label, price, qty = pick_product()
        item_total = round(price * qty, 2)
        total_amount += item_total

        purchase_recs.append({
            "user_id":        customer_id,
            "user_name":      customer[0],
            "user_email":     customer[1],
            "product_id":     f"prod_{pname.replace(' ','_').lower()[:20]}",
            "product_name":   pname,
            "category":       cat,
            "variant":        variant_label,
            "quantity":       qty,
            "price":          price,
            "total":          item_total,
            "sold_by":        worker_id,
            "sold_by_name":   worker_name,
            "purchase_date":  ts,
            "payment_status": "completed",
        })
        line_items.append({
            "product_name": pname,
            "variant":      variant_label,
            "quantity":     qty,
            "price":        price,
            "total":        item_total,
        })

    products_sold_doc = {
        "customer_id":    customer_id,
        "customer_name":  customer[0],
        "customer_email": customer[1],
        "items":          line_items,
        "total_amount":   round(total_amount, 2),
        "sold_by":        worker_id,
        "sold_by_name":   worker_name,
        "sale_date":      ts,
    }
    return purchase_recs, products_sold_doc

# ──────────────────────────────────────────────
# Generate date range: TODAY going back 77 days
# ──────────────────────────────────────────────
now   = datetime.datetime.now()
today = now.replace(hour=0, minute=0, second=0, microsecond=0)

all_purchase_docs = []
all_sold_docs     = []

print(f"\n[INFO] Generating transactions for last 77 days…")

for days_ago in range(77, -1, -1):          # 77 → 0 (inclusive of today)
    base_date = today - datetime.timedelta(days=days_ago)

    # More orders in recent days, fewer older ones
    if days_ago == 0:
        n_orders = random.randint(6, 12)        # today: busy
    elif days_ago <= 7:
        n_orders = random.randint(5, 10)        # last week: high
    elif days_ago <= 30:
        n_orders = random.randint(3, 8)         # last month: moderate
    else:
        n_orders = random.randint(1, 5)         # 30–77 days ago: lighter

    for _ in range(n_orders):
        ts = random_time(base_date)
        precs, psold = build_transaction(ts)
        all_purchase_docs.extend(precs)
        all_sold_docs.append(psold)

# ──────────────────────────────────────────────
# Preview totals before inserting
# ──────────────────────────────────────────────
total_rev = sum(d["total"] for d in all_purchase_docs)
today_rev = sum(d["total"] for d in all_purchase_docs
                if d["purchase_date"] >= today)
today_orders = sum(1 for d in all_sold_docs if d["sale_date"] >= today)

print(f"\n[PREVIEW] Documents to insert:")
print(f"  user_data_bought rows : {len(all_purchase_docs):>6,}")
print(f"  products_sold rows    : {len(all_sold_docs):>6,}")
print(f"  Total revenue (all)   : ₹{total_rev:>10,.2f}")
print(f"  Today's revenue       : ₹{today_rev:>10,.2f}")
print(f"  Today's orders        : {today_orders}")

if total_rev < 50000:
    # Safety: scale up prices by multiplying totals automatically
    factor = 50001 / total_rev * 1.3  # aim for 30% above threshold
    print(f"\n[WARN] Revenue below ₹50,000 — scaling by {factor:.2f}x")
    for d in all_purchase_docs:
        d["price"] = round(d["price"] * factor, 2)
        d["total"] = round(d["total"] * factor, 2)
    for d in all_sold_docs:
        d["total_amount"] = round(d["total_amount"] * factor, 2)
        for item in d["items"]:
            item["price"] = round(item["price"] * factor, 2)
            item["total"] = round(item["total"] * factor, 2)
    total_rev = sum(d["total"] for d in all_purchase_docs)
    print(f"  Scaled total revenue  : ₹{total_rev:>10,.2f}")

# ──────────────────────────────────────────────
# Ask for confirmation before writing
# ──────────────────────────────────────────────
resp = input("\nProceed with insertion? [y/N] ").strip().lower()
if resp != "y":
    print("[ABORT] Nothing written.")
    sys.exit(0)

# ──────────────────────────────────────────────
# Insert in bulk
# ──────────────────────────────────────────────
print("\n[INFO] Inserting user_data_bought …")
result1 = user_data_bought.insert_many(all_purchase_docs, ordered=False)
print(f"[OK]   Inserted {len(result1.inserted_ids):,} purchase line-items")

print("[INFO] Inserting products_sold …")
result2 = products_sold_col.insert_many(all_sold_docs, ordered=False)
print(f"[OK]   Inserted {len(result2.inserted_ids):,} sale transactions")

# ──────────────────────────────────────────────
# Final summary
# ──────────────────────────────────────────────
final_total  = user_data_bought.aggregate([
    {"$group": {"_id": None, "t": {"$sum": "$total"}}}
])
final_today  = user_data_bought.aggregate([
    {"$match": {"purchase_date": {"$gte": today}}},
    {"$group": {"_id": None, "t": {"$sum": "$total"}}}
])
ft = list(final_total)
fd = list(final_today)

print("\n" + "="*55)
print("  DATABASE TOTALS (after insert)")
print("="*55)
print(f"  Total Revenue (all time) : ₹{ft[0]['t']:>10,.2f}" if ft else "  No data found")
print(f"  Today's Revenue          : ₹{fd[0]['t']:>10,.2f}" if fd else "  Today: ₹0")
print(f"  Total Sale Transactions  : {products_sold_col.count_documents({}):>6,}")
print(f"  Total Purchase Line-Items: {user_data_bought.count_documents({}):>6,}")
print("="*55)
print("\n[DONE] Refresh the analytics dashboard to see the data.")
