"""
Script to add static purchase history to users
Adds random product purchases to users so they have buying history
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
from bson import ObjectId

load_dotenv()

def main():
    print("="*70)
    print("ADDING PURCHASE HISTORY TO USERS")
    print("="*70)
    
    # Connect to MongoDB
    MONGODB_URL = os.getenv('MONGODB_URL')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')
    
    print(f"Connecting to MongoDB...")
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    
    users_collection = db['users']
    products_collection = db['products_update']
    products_sold_collection = db['products_sold']
    
    # Get all users and products
    users = list(users_collection.find())
    products = list(products_collection.find())
    
    print(f"\n✅ Found {len(users)} users")
    print(f"✅ Found {len(products)} products")
    print(f"\n📦 Adding purchase history...\n")
    
    total_purchases = 0
    users_with_purchases = 0
    
    # Add purchases to 70% of users (randomly)
    for user in users:
        # 70% chance to add purchases to this user
        if random.random() < 0.7:
            # Each user gets 1-5 purchases
            num_purchases = random.randint(1, 5)
            user_purchases = []
            
            for _ in range(num_purchases):
                # Select random product
                product = random.choice(products)
                
                # Select random variant
                variants = product.get('variants', [])
                if not variants:
                    continue
                
                variant = random.choice(variants)
                
                # Generate random purchase date (last 90 days)
                days_ago = random.randint(0, 90)
                purchase_date = datetime.now() - timedelta(days=days_ago)
                
                # Random quantity (1-3)
                quantity = random.randint(1, 3)
                
                # Calculate total
                price = float(variant.get('price', 0))
                total = price * quantity
                
                # Create purchase record
                purchase = {
                    'user_id': user['_id'],
                    'user_name': user.get('name', 'Unknown'),
                    'user_email': user.get('email', 'unknown@example.com'),
                    'product_id': product['_id'],
                    'product_name': product.get('name', 'Unknown Product'),
                    'variant': variant.get('name', 'Default'),
                    'sku': variant.get('sku', 'N/A'),
                    'price': price,
                    'quantity': quantity,
                    'total': total,
                    'date': purchase_date,
                    'status': 'completed'
                }
                
                # Insert into products_sold
                products_sold_collection.insert_one(purchase)
                user_purchases.append({
                    'product': product.get('name'),
                    'variant': variant.get('name'),
                    'quantity': quantity,
                    'total': total
                })
                
                total_purchases += 1
            
            users_with_purchases += 1
            
            # Show progress every 100 users
            if users_with_purchases % 100 == 0:
                print(f"Progress: {users_with_purchases} users with purchases added...")
    
    print(f"\n✅ Successfully added purchase history!")
    print(f"📊 Statistics:")
    print(f"   - Users with purchases: {users_with_purchases}/{len(users)} ({(users_with_purchases/len(users)*100):.1f}%)")
    print(f"   - Total purchases created: {total_purchases}")
    print(f"   - Average purchases per user: {total_purchases/users_with_purchases:.1f}")
    
    # Show sample purchases
    print(f"\n📋 Sample purchases:")
    sample_purchases = list(products_sold_collection.find().limit(5))
    for i, purchase in enumerate(sample_purchases, 1):
        print(f"{i}. {purchase.get('user_name')} bought {purchase.get('quantity')}x {purchase.get('product_name')} ({purchase.get('variant')}) - ₹{purchase.get('total'):.2f}")
    
    print("\n" + "="*70)
    print("✅ PURCHASE HISTORY ADDED SUCCESSFULLY!")
    print("="*70)

if __name__ == '__main__':
    main()
