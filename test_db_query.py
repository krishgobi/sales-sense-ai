from pymongo import MongoClient
import os

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['groceries_db']
bought = db['user_data_bought']

# Count total records
total = bought.count_documents({})
print(f"Total records: {total}")

# Find top 5 products by revenue
top = list(bought.aggregate([
    {'$group': {'_id': '$product_name', 'total_revenue': {'$sum': '$total'}, 'units': {'$sum': '$quantity'}}},
    {'$sort': {'total_revenue': -1}},
    {'$limit': 5}
]))

print(f"\nTop 5 products by revenue:")
for p in top:
    print(f"  {p['_id']}: Rs{p['total_revenue']:.2f} ({p['units']} units)")
