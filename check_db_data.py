import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]

# Example: Get all users
def get_all_users():
    return list(db.users.find({}, {'_id': 0}))

# Example: Get all products
def get_all_products():
    return list(db.products_update.find({}, {'_id': 0}))

# Example: Get all sales
def get_all_sales():
    return list(db.user_data_bought.find({}, {'_id': 0}))

# Example: Get dashboard summary
def get_dashboard_summary():
    total_revenue = db.user_data_bought.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
    ])
    total_orders = db.user_data_bought.count_documents({})
    total_products = db.products_update.count_documents({})
    total_users = db.users.count_documents({})
    return {
        'total_revenue': next(total_revenue, {'total': 0})['total'],
        'total_orders': total_orders,
        'total_products': total_products,
        'total_users': total_users
    }

if __name__ == '__main__':
    print('--- Dashboard Summary ---')
    print(get_dashboard_summary())
    print('\n--- All Users ---')
    print(get_all_users()[:5])  # Show first 5 users
    print('\n--- All Products ---')
    print(get_all_products()[:5])  # Show first 5 products
    print('\n--- All Sales ---')
    print(get_all_sales()[:5])  # Show first 5 sales
