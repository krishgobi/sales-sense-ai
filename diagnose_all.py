from dotenv import load_dotenv
import os, pymongo, datetime, random
load_dotenv()
db = pymongo.MongoClient(os.getenv("MONGODB_URL")).saless

# Check today's data
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
count_today = db.user_data_bought.count_documents({"purchase_date": {"$gte": today}})
print("Today purchase records:", count_today)

# Check recent days
for i in range(7):
    d = today - datetime.timedelta(days=i)
    c = db.user_data_bought.count_documents({"purchase_date": {"$gte": d, "$lt": d + datetime.timedelta(days=1)}})
    print(f"  {d.strftime('%d %b')}: {c} records")

# Check user list
print("\nUsers sample:")
for u in db.users_update.find({}, {"name":1, "email":1, "phone":1, "_id":1}).limit(5):
    print(f"  {u.get('name')} | {u.get('email')} | {u.get('phone')}")

# Check products available
print("\nProducts sample (for seeding):")
all_products = []
for col_name in ["products_update", "products"]:
    for p in db[col_name].find({}, {"name":1, "category":1, "variants":1, "_id":1}):
        if p.get("variants"):
            all_products.append(p)
print(f"  Total products with variants: {len(all_products)}")
if all_products:
    p = all_products[0]
    print(f"  Sample: {p.get('name')} | variants: {p.get('variants', [])[:1]}")

# Check workers
print("\nWorkers:")
for w in db.workers_update.find({}, {"name":1, "email":1, "password":1, "_id":1}):
    print(f"  {w.get('name')} | {w.get('email')} | pass={w.get('password')} | id={w['_id']}")
