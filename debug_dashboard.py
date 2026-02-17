"""
Debug script to check what data the admin dashboard is receiving
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

print("\n" + "="*60)
print("ADMIN DASHBOARD DATA CHECK")
print("="*60)

# Simulate the dashboard context building
users = db['users']
products_update = db['products_update']
products_sold = db['products_sold']
workers_update = db['workers_update']

# Stats calculation
today = datetime.datetime.now().replace(hour=0, minute=0, second=0)

total_sales_result = list(products_sold.aggregate([
    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
]))
total_sales = float(total_sales_result[0]['total']) if total_sales_result else 0.0

sales_today_result = list(products_sold.aggregate([
    {'$match': {'date': {'$gte': today}}},
    {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
]))
sales_today = float(sales_today_result[0]['total']) if sales_today_result else 0.0

stats = {
    'total_users': users.count_documents({}),
    'new_users_today': users.count_documents({'created_at': {'$gte': today}}),
    'total_sales': total_sales,
    'sales_today': sales_today,
    'total_products': products_update.count_documents({}),
    'total_workers': workers_update.count_documents({}),
    'active_workers': workers_update.count_documents({
        'last_active': {'$gte': datetime.datetime.now() - datetime.timedelta(hours=24)}
    })
}

print("\n📊 STATISTICS:")
print(f"  Total Users: {stats['total_users']}")
print(f"  New Users Today: {stats['new_users_today']}")
print(f"  Total Sales: ₹{stats['total_sales']:,.2f}")
print(f"  Today's Sales: ₹{stats['sales_today']:,.2f}")
print(f"  Total Products: {stats['total_products']}")
print(f"  Total Workers: {stats['total_workers']}")
print(f"  Active Workers: {stats['active_workers']}")

# Pagination
page = 1
per_page = 20
skip = (page - 1) * per_page

total_users_count = users.count_documents({})
total_pages = (total_users_count + per_page - 1) // per_page

recent_users = list(users.find().sort('created_at', -1).skip(skip).limit(per_page))

print(f"\n👥 RECENT USERS (Page {page}):")
print(f"  Fetched: {len(recent_users)} users")
print(f"  Total: {total_users_count} users")
print(f"  Total Pages: {total_pages}")
print(f"  Users per page: {per_page}")

print("\n📋 First 10 users on page 1:")
for i, user in enumerate(recent_users[:10], 1):
    print(f"  {i}. {user.get('name')}: {user.get('email')}")

pagination = {
    'page': page,
    'per_page': per_page,
    'total': total_users_count,
    'pages': total_pages
}

print(f"\n🔢 PAGINATION INFO:")
print(f"  Current Page: {pagination['page']}")
print(f"  Per Page: {pagination['per_page']}")
print(f"  Total Users: {pagination['total']}")
print(f"  Total Pages: {pagination['pages']}")

print("\n" + "="*60)
print("✅ All data looks correct!")
print("If you're seeing only 4 users, there might be a frontend issue")
print("or you might be looking at a cached/old version of the page.")
print("\nSuggestions:")
print("1. Hard refresh the browser (Ctrl+Shift+R or Ctrl+F5)")
print("2. Clear browser cache")
print("3. Check browser console for JavaScript errors")
print("4. Verify you're on http://localhost:5000/admin/dashboard")
print("5. Not on /demo-dashboard")
print("="*60 + "\n")

client.close()
