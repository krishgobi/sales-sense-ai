import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection - use the same variable names as in app.py
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'sales_sense')

print(f"Connecting to MongoDB...")
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]
print(f"Connected to database: {MONGODB_DATABASE}\n")

# Collections
users = db['users']
products_update = db['products_update']
products_sold = db['products_sold']

# Sample data
first_names = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
    'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen',
    'Christopher', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
    'Donald', 'Ashley', 'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa', 'Edward', 'Deborah',
    'Ronald', 'Stephanie', 'Timothy', 'Rebecca', 'Jason', 'Sharon', 'Jeffrey', 'Laura', 'Ryan', 'Cynthia',
    'Jacob', 'Kathleen', 'Gary', 'Amy', 'Nicholas', 'Shirley', 'Eric', 'Angela', 'Jonathan', 'Helen',
    'Stephen', 'Anna', 'Larry', 'Brenda', 'Justin', 'Pamela', 'Scott', 'Nicole', 'Brandon', 'Emma',
    'Benjamin', 'Samantha', 'Samuel', 'Katherine', 'Raymond', 'Christine', 'Gregory', 'Debra', 'Frank', 'Rachel',
    'Alexander', 'Catherine', 'Patrick', 'Carolyn', 'Raymond', 'Janet', 'Jack', 'Ruth', 'Dennis', 'Maria'
]

last_names = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
    'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts',
    'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes',
    'Stewart', 'Morris', 'Morales', 'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper',
    'Peterson', 'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
    'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz', 'Hughes',
    'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long', 'Ross', 'Foster', 'Jimenez'
]

cities = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
    'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco',
    'Indianapolis', 'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit', 'Portland',
    'Las Vegas', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Sacramento',
    'Kansas City', 'Long Beach', 'Mesa', 'Atlanta', 'Colorado Springs', 'Virginia Beach', 'Raleigh', 'Omaha',
    'Miami', 'Oakland', 'Minneapolis', 'Tulsa', 'Wichita', 'New Orleans', 'Arlington', 'Cleveland'
]

states = [
    'NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA', 'TX', 'FL', 'TX', 'OH', 'NC', 'CA',
    'IN', 'WA', 'CO', 'DC', 'MA', 'TX', 'TN', 'MI', 'OR', 'NV', 'TN', 'KY', 'MD', 'WI', 'NM', 'AZ',
    'CA', 'CA', 'MO', 'CA', 'AZ', 'GA', 'CO', 'VA', 'NC', 'NE', 'FL', 'CA', 'MN', 'OK', 'KS', 'LA',
    'TX', 'OH'
]

def generate_phone():
    """Generate a random US phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

def generate_email(first_name, last_name):
    """Generate an email address"""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'aol.com']
    separators = ['', '.', '_']
    numbers = ['', str(random.randint(1, 999))]
    
    sep = random.choice(separators)
    num = random.choice(numbers)
    domain = random.choice(domains)
    
    return f"{first_name.lower()}{sep}{last_name.lower()}{num}@{domain}"

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_dummy_users(num_users=550):
    """Create dummy users with realistic data"""
    print(f"Creating {num_users} dummy users...")
    
    # Date range for user creation (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    dummy_users = []
    
    for i in range(num_users):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        city_index = random.randint(0, len(cities) - 1)
        
        join_date = generate_random_date(start_date, end_date)
        
        user = {
            'name': f"{first_name} {last_name}",
            'email': generate_email(first_name, last_name),
            'phone': generate_phone(),
            'address': f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar', 'Elm', 'Washington', 'Lake', 'Hill', 'Park'])} {random.choice(['St', 'Ave', 'Blvd', 'Rd', 'Dr', 'Ln', 'Way', 'Ct'])}",
            'city': cities[city_index],
            'state': states[city_index],
            'zipcode': str(random.randint(10000, 99999)),
            'join_date': join_date,
            'created_at': join_date,
            'is_active': random.choice([True, True, True, True, False]),  # 80% active
            'loyalty_points': random.randint(0, 5000),
            'total_purchases': 0,  # Will be updated after creating sales
            'last_purchase': None
        }
        
        dummy_users.append(user)
        
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1} users...")
    
    # Insert users into database
    print("Inserting users into database...")
    result = users.insert_many(dummy_users)
    print(f"Successfully inserted {len(result.inserted_ids)} users!")
    
    return result.inserted_ids

def create_dummy_sales(user_ids):
    """Create dummy sales/purchases for users"""
    print("Creating dummy sales data...")
    
    # Get all products
    all_products = list(products_update.find())
    if not all_products:
        print("No products found! Please add products first.")
        return
    
    print(f"Found {len(all_products)} products")
    
    # Date range for sales (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    dummy_sales = []
    user_purchase_count = {}
    user_last_purchase = {}
    
    for user_id in user_ids:
        # Each user makes between 1 to 15 purchases
        num_purchases = random.choices(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            weights=[5, 10, 15, 20, 15, 10, 8, 7, 5, 3, 1, 0.5, 0.3, 0.1, 0.05, 0.05]
        )[0]
        
        user_purchase_count[str(user_id)] = num_purchases
        
        for _ in range(num_purchases):
            # Select random product
            product = random.choice(all_products)
            
            # Select random variant
            if 'variants' in product and product['variants']:
                variant = random.choice(product['variants'])
                
                # Random quantity (1-5, with higher weight on lower quantities)
                quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3])[0]
                
                # Generate random sale date
                sale_date = generate_random_date(start_date, end_date)
                
                # Store latest purchase date
                if str(user_id) not in user_last_purchase or sale_date > user_last_purchase[str(user_id)]:
                    user_last_purchase[str(user_id)] = sale_date
                
                # Calculate price
                price = float(variant.get('price', 0))
                total = price * quantity
                
                sale = {
                    'user_id': str(user_id),
                    'product_id': str(product['_id']),
                    'product_name': product['name'],
                    'variant_name': variant.get('name', 'Default'),
                    'quantity': quantity,
                    'price': price,
                    'total': total,
                    'date': sale_date,
                    'status': random.choice(['completed', 'completed', 'completed', 'completed', 'pending', 'cancelled']),
                    'payment_method': random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Cash', 'Apple Pay', 'Google Pay']),
                    'created_at': sale_date
                }
                
                dummy_sales.append(sale)
    
    # Insert sales into database
    if dummy_sales:
        print(f"Inserting {len(dummy_sales)} sales records...")
        products_sold.insert_many(dummy_sales)
        print(f"Successfully inserted {len(dummy_sales)} sales!")
        
        # Update user purchase counts and last purchase dates
        print("Updating user purchase statistics...")
        for user_id_str, count in user_purchase_count.items():
            update_data = {'total_purchases': count}
            if user_id_str in user_last_purchase:
                update_data['last_purchase'] = user_last_purchase[user_id_str]
            
            users.update_one(
                {'_id': ObjectId(user_id_str)},
                {'$set': update_data}
            )
        print("User statistics updated!")
    else:
        print("No sales to insert!")

def display_statistics():
    """Display database statistics"""
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    total_users = users.count_documents({})
    total_products = products_update.count_documents({})
    total_sales = products_sold.count_documents({})
    
    print(f"Total Users: {total_users}")
    print(f"Total Products: {total_products}")
    print(f"Total Sales: {total_sales}")
    
    # Calculate total revenue
    total_revenue = 0
    for sale in products_sold.find():
        try:
            if isinstance(sale.get('total'), (int, float)):
                total_revenue += float(sale['total'])
            elif isinstance(sale.get('price'), (int, float)) and isinstance(sale.get('quantity'), (int, float)):
                total_revenue += float(sale['price']) * float(sale['quantity'])
        except:
            pass
    
    print(f"Total Revenue: ${total_revenue:,.2f}")
    
    # Active users
    active_users = users.count_documents({'is_active': True})
    print(f"Active Users: {active_users}")
    
    # Users with purchases
    users_with_purchases = users.count_documents({'total_purchases': {'$gt': 0}})
    print(f"Users with Purchases: {users_with_purchases}")
    
    print("="*60 + "\n")

def main():
    """Main function to generate all dummy data"""
    print("\n" + "="*60)
    print("DUMMY DATA GENERATOR FOR SALES SENSE AI")
    print("="*60 + "\n")
    
    # Check if products exist
    product_count = products_update.count_documents({})
    if product_count == 0:
        print("ERROR: No products found in database!")
        print("Please add products first before generating dummy data.")
        return
    
    print(f"Found {product_count} products in database.\n")
    
    print("⚠️  WARNING: This will create 550 dummy users with purchase data!")
    print("Starting generation in 3 seconds...")
    import time
    time.sleep(3)
    
    # Generate users
    user_ids = create_dummy_users(550)
    
    # Generate sales
    create_dummy_sales(user_ids)
    
    # Display statistics
    display_statistics()
    
    print("✅ Dummy data generation completed successfully!")
    print("You can now view the reports in the admin dashboard.\n")

if __name__ == '__main__':
    main()
