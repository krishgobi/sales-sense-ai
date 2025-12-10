import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')

print(f"Connecting to MongoDB...")
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]
print(f"Connected to database: {MONGODB_DATABASE}\n")

# Collections
users = db['users']
products_update = db['products_update']
products_sold = db['products_sold']

# Expanded sample data for more variety
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
    'Alexander', 'Catherine', 'Patrick', 'Carolyn', 'Jack', 'Ruth', 'Dennis', 'Maria', 'Jerry', 'Heather',
    'Tyler', 'Diane', 'Aaron', 'Virginia', 'Jose', 'Julie', 'Adam', 'Joyce', 'Henry', 'Victoria',
    'Nathan', 'Olivia', 'Douglas', 'Kelly', 'Zachary', 'Christina', 'Peter', 'Lauren', 'Kyle', 'Joan',
    'Walter', 'Evelyn', 'Ethan', 'Judith', 'Jeremy', 'Megan', 'Harold', 'Cheryl', 'Keith', 'Andrea',
    'Christian', 'Hannah', 'Roger', 'Jacqueline', 'Noah', 'Martha', 'Gerald', 'Gloria', 'Carl', 'Teresa',
    'Terry', 'Ann', 'Sean', 'Sara', 'Austin', 'Madison', 'Arthur', 'Frances', 'Lawrence', 'Kathryn'
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
    'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long', 'Ross', 'Foster', 'Jimenez',
    'Powell', 'Jenkins', 'Perry', 'Russell', 'Sullivan', 'Bell', 'Coleman', 'Butler', 'Henderson', 'Barnes',
    'Gonzales', 'Fisher', 'Vasquez', 'Simmons', 'Romero', 'Jordan', 'Patterson', 'Alexander', 'Hamilton', 'Graham'
]

cities = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
    'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco',
    'Indianapolis', 'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit', 'Portland',
    'Las Vegas', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Sacramento',
    'Kansas City', 'Long Beach', 'Mesa', 'Atlanta', 'Colorado Springs', 'Virginia Beach', 'Raleigh', 'Omaha',
    'Miami', 'Oakland', 'Minneapolis', 'Tulsa', 'Wichita', 'New Orleans', 'Arlington', 'Cleveland',
    'Tampa', 'Bakersfield', 'Aurora', 'Anaheim', 'Honolulu', 'Santa Ana', 'Riverside', 'Corpus Christi',
    'Lexington', 'Stockton', 'Henderson', 'Saint Paul', 'Cincinnati', 'Pittsburgh', 'Greensboro', 'Anchorage',
    'Plano', 'Lincoln', 'Orlando', 'Irvine', 'Newark', 'Durham', 'Chula Vista', 'Toledo', 'Fort Wayne',
    'St. Petersburg', 'Laredo', 'Jersey City', 'Chandler', 'Madison', 'Lubbock', 'Scottsdale', 'Reno'
]

states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'CA', 'TX', 'CA', 'TX', 'FL', 'OH', 'NC', 'CA', 
          'IN', 'WA', 'CO', 'DC', 'MA', 'TN', 'MI', 'OR', 'NV', 'TN', 'KY', 'MD', 'WI', 'NM',
          'CA', 'MO', 'CA', 'AZ', 'GA', 'CO', 'VA', 'NC', 'NE', 'FL', 'CA', 'MN', 'OK', 'KS',
          'FL', 'CA', 'TX', 'CA', 'HI', 'CA', 'TX', 'KY', 'CA', 'NV', 'MN', 'OH', 'PA', 'NC',
          'AK', 'TX', 'NE', 'FL', 'CA', 'NJ', 'NC', 'CA', 'OH', 'IN', 'FL', 'TX', 'NJ', 'AZ',
          'WI', 'TX', 'AZ', 'NV']

def generate_phone():
    """Generate a random US phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

def generate_email(first_name, last_name, num):
    """Generate an email address"""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'aol.com', 'protonmail.com', 'mail.com']
    separators = ['', '.', '_', '-']
    
    sep = random.choice(separators)
    domain = random.choice(domains)
    
    # Ensure unique emails
    return f"{first_name.lower()}{sep}{last_name.lower()}{num}@{domain}"

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_large_user_dataset(num_users=1500):
    """Create a large dataset of dummy users"""
    print(f"Creating {num_users} dummy users...")
    
    # Date range for user creation (last 3 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)  # 3 years
    
    dummy_users = []
    
    for i in range(num_users):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        city_index = random.randint(0, min(len(cities), len(states)) - 1)
        
        join_date = generate_random_date(start_date, end_date)
        
        user = {
            'name': f"{first_name} {last_name}",
            'email': generate_email(first_name, last_name, i+1000),  # Start from 1000 to avoid conflicts
            'phone': generate_phone(),
            'address': f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar', 'Elm', 'Washington', 'Lake', 'Hill', 'Park', 'River', 'Forest', 'Sunset', 'Spring'])} {random.choice(['St', 'Ave', 'Blvd', 'Rd', 'Dr', 'Ln', 'Way', 'Ct', 'Pl', 'Ter'])}",
            'city': cities[city_index] if city_index < len(cities) else random.choice(cities),
            'state': states[city_index] if city_index < len(states) else random.choice(states),
            'zipcode': str(random.randint(10000, 99999)),
            'join_date': join_date,
            'created_at': join_date,
            'is_active': random.choice([True, True, True, True, True, False]),  # 83% active
            'loyalty_points': random.randint(0, 8000),
            'total_purchases': 0,
            'last_purchase': None
        }
        
        dummy_users.append(user)
        
        if (i + 1) % 250 == 0:
            print(f"Generated {i + 1} users...")
    
    # Insert users in batches for better performance
    print("Inserting users into database (in batches)...")
    batch_size = 100
    inserted_ids = []
    
    for i in range(0, len(dummy_users), batch_size):
        batch = dummy_users[i:i + batch_size]
        result = users.insert_many(batch)
        inserted_ids.extend(result.inserted_ids)
        print(f"Inserted batch {i//batch_size + 1}/{(len(dummy_users) + batch_size - 1)//batch_size}")
    
    print(f"Successfully inserted {len(inserted_ids)} users!")
    return inserted_ids

def create_bulk_sales(user_ids, num_sales_target=5000):
    """Create bulk sales/purchases for users"""
    print(f"\nCreating approximately {num_sales_target} sales records...")
    
    # Get all products
    all_products = list(products_update.find())
    if not all_products:
        print("No products found! Please add products first.")
        return
    
    print(f"Found {len(all_products)} products")
    
    # Date range for sales (last 3 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)
    
    dummy_sales = []
    user_purchase_count = {}
    user_last_purchase = {}
    
    sales_created = 0
    
    for user_id in user_ids:
        # Each user makes between 0 to 20 purchases (weighted distribution)
        num_purchases = random.choices(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            weights=[8, 15, 20, 18, 15, 10, 7, 5, 4, 3, 2, 1.5, 1, 0.8, 0.5, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02]
        )[0]
        
        user_purchase_count[str(user_id)] = num_purchases
        
        for _ in range(num_purchases):
            # Select random product
            product = random.choice(all_products)
            
            # Select random variant
            if 'variants' in product and product['variants']:
                variant = random.choice(product['variants'])
                
                # Random quantity (weighted towards lower quantities)
                quantity = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[45, 25, 15, 8, 4, 2, 0.8, 0.2])[0]
                
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
                    'variant_name': variant.get('name', variant.get('quantity', 'Default')),
                    'quantity': quantity,
                    'price': price,
                    'total': total,
                    'date': sale_date,
                    'status': random.choice(['completed', 'completed', 'completed', 'completed', 'completed', 'pending', 'cancelled']),
                    'payment_method': random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Cash', 'Apple Pay', 'Google Pay', 'Venmo']),
                    'created_at': sale_date
                }
                
                dummy_sales.append(sale)
                sales_created += 1
        
        if sales_created >= num_sales_target:
            break
    
    # Insert sales in batches
    if dummy_sales:
        print(f"\nInserting {len(dummy_sales)} sales records (in batches)...")
        batch_size = 500
        
        for i in range(0, len(dummy_sales), batch_size):
            batch = dummy_sales[i:i + batch_size]
            products_sold.insert_many(batch)
            print(f"Inserted batch {i//batch_size + 1}/{(len(dummy_sales) + batch_size - 1)//batch_size}")
        
        print(f"Successfully inserted {len(dummy_sales)} sales!")
        
        # Update user purchase counts
        print("\nUpdating user purchase statistics...")
        update_count = 0
        for user_id_str, count in user_purchase_count.items():
            update_data = {'total_purchases': count}
            if user_id_str in user_last_purchase:
                update_data['last_purchase'] = user_last_purchase[user_id_str]
            
            users.update_one(
                {'_id': ObjectId(user_id_str)},
                {'$set': update_data}
            )
            update_count += 1
            
            if update_count % 250 == 0:
                print(f"Updated {update_count} users...")
        
        print("User statistics updated!")
    else:
        print("No sales to insert!")

def display_statistics():
    """Display database statistics"""
    print("\n" + "="*70)
    print("FINAL DATABASE STATISTICS")
    print("="*70)
    
    total_users = users.count_documents({})
    total_products = products_update.count_documents({})
    total_sales = products_sold.count_documents({})
    
    print(f"Total Users: {total_users:,}")
    print(f"Total Products: {total_products:,}")
    print(f"Total Sales: {total_sales:,}")
    
    # Calculate total revenue
    total_revenue = 0
    for sale in products_sold.find():
        try:
            if isinstance(sale.get('total'), (int, float)):
                total_revenue += float(sale['total'])
        except:
            pass
    
    print(f"Total Revenue: ${total_revenue:,.2f}")
    
    # Active users
    active_users = users.count_documents({'is_active': True})
    print(f"Active Users: {active_users:,}")
    
    # Users with purchases
    users_with_purchases = users.count_documents({'total_purchases': {'$gt': 0}})
    print(f"Users with Purchases: {users_with_purchases:,}")
    
    # Average purchases per user
    if users_with_purchases > 0:
        avg_purchases = total_sales / users_with_purchases
        print(f"Average Purchases per User: {avg_purchases:.2f}")
    
    print("="*70 + "\n")

def main():
    """Main function to generate large dataset"""
    print("\n" + "="*70)
    print("LARGE SCALE DUMMY DATA GENERATOR FOR SALES SENSE AI")
    print("="*70 + "\n")
    
    # Check current data
    current_users = users.count_documents({})
    current_sales = products_sold.count_documents({})
    
    print(f"Current Database Status:")
    print(f"  - Users: {current_users:,}")
    print(f"  - Sales: {current_sales:,}\n")
    
    # Check if products exist
    product_count = products_update.count_documents({})
    if product_count == 0:
        print("ERROR: No products found in database!")
        return
    
    print(f"Found {product_count} products in database.\n")
    
    print("⚠️  WARNING: This will add 1500 more users and 5000+ sales records!")
    print("This will make your database look very professional with lots of data.")
    print("Starting generation in 3 seconds...\n")
    
    import time
    time.sleep(3)
    
    # Generate users
    user_ids = create_large_user_dataset(1500)
    
    # Generate sales
    create_bulk_sales(user_ids, 5000)
    
    # Display statistics
    display_statistics()
    
    print("✅ Large scale data generation completed successfully!")
    print("Your admin dashboard will now show impressive amounts of data!\n")

if __name__ == '__main__':
    main()
