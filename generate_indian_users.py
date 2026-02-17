"""
Generate 50+ Indian users with realistic data
"""
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'sales_sense')

print(f"Connecting to MongoDB...")
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]
users = db['users']

# Indian first names (mix of traditional and modern)
indian_first_names = [
    # Male names
    'Rajesh', 'Amit', 'Suresh', 'Vijay', 'Ramesh', 'Arun', 'Prakash', 'Kumar', 'Ravi', 'Sanjay',
    'Ashok', 'Rakesh', 'Mahesh', 'Deepak', 'Manoj', 'Ajay', 'Rahul', 'Rohan', 'Arjun', 'Karan',
    'Varun', 'Nikhil', 'Akhil', 'Vivek', 'Ankit', 'Vishal', 'Sachin', 'Rohit', 'Virat', 'Hardik',
    # Female names
    'Priya', 'Lakshmi', 'Kavita', 'Anita', 'Sunita', 'Radha', 'Savita', 'Meera', 'Geeta', 'Sita',
    'Anjali', 'Neha', 'Pooja', 'Divya', 'Sneha', 'Riya', 'Simran', 'Shruti', 'Aditi', 'Aishwarya',
    'Deepika', 'Ananya', 'Ishita', 'Tanvi', 'Aarti', 'Jyoti', 'Rekha', 'Poonam', 'Madhuri', 'Swati'
]

# Indian last names
indian_last_names = [
    'Sharma', 'Kumar', 'Singh', 'Patel', 'Reddy', 'Nair', 'Iyer', 'Rao', 'Pillai', 'Gupta',
    'Verma', 'Agarwal', 'Joshi', 'Shah', 'Mehta', 'Desai', 'Kulkarni', 'Jain', 'Shetty', 'Chopra',
    'Kapoor', 'Malhotra', 'Bhatia', 'Sethi', 'Khanna', 'Bansal', 'Mittal', 'Arora', 'Saxena', 'Srivastava',
    'Chaudhary', 'Chauhan', 'Yadav', 'Pandey', 'Mishra', 'Tiwari', 'Dubey', 'Shukla', 'Thakur', 'Menon',
    'Krishnan', 'Subramanian', 'Venkatesh', 'Narayanan', 'Raman', 'Bose', 'Das', 'Roy', 'Mukherjee', 'Chatterjee'
]

# Indian cities
indian_cities = [
    'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad',
    'Jaipur', 'Lucknow', 'Surat', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal',
    'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad',
    'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar', 'Allahabad',
    'Ranchi', 'Howrah', 'Coimbatore', 'Jabalpur', 'Gwalior', 'Vijayawada', 'Jodhpur', 'Madurai'
]

# Indian states
indian_states = [
    'Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'West Bengal', 'Telangana', 'Gujarat',
    'Rajasthan', 'Uttar Pradesh', 'Madhya Pradesh', 'Andhra Pradesh', 'Punjab', 'Haryana',
    'Bihar', 'Odisha', 'Kerala', 'Jharkhand', 'Assam', 'Chhattisgarh', 'Uttarakhand'
]

# Indian street names
street_prefixes = [
    'MG Road', 'Gandhi Nagar', 'Nehru Street', 'Park Avenue', 'Main Road', 'Anna Salai',
    'Brigade Road', 'Commercial Street', 'Residency Road', 'Link Road', 'Station Road',
    'Railway Road', 'Market Street', 'Temple Street', 'Church Street', 'Beach Road',
    'Ring Road', 'Bypass Road', 'Highway Road', 'Avenue Road'
]

def generate_indian_phone():
    """Generate a realistic Indian phone number"""
    # Indian mobile numbers start with 6, 7, 8, or 9
    return f"+91-{random.choice([6, 7, 8, 9])}{random.randint(100000000, 999999999)}"

def generate_indian_email(first_name, last_name):
    """Generate an Indian email address"""
    domains = ['gmail.com', 'yahoo.co.in', 'outlook.com', 'hotmail.com', 'rediffmail.com']
    separators = ['', '.', '_']
    numbers = ['', str(random.randint(1, 999))]
    
    sep = random.choice(separators)
    num = random.choice(numbers)
    domain = random.choice(domains)
    
    return f"{first_name.lower()}{sep}{last_name.lower()}{num}@{domain}"

def generate_indian_pincode():
    """Generate a realistic Indian pincode (6 digits)"""
    return str(random.randint(100000, 999999))

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_indian_users(num_users=50):
    """Create dummy Indian users with realistic data"""
    print(f"\nCreating {num_users} Indian users...")
    
    # Check existing users
    existing_count = users.count_documents({})
    print(f"Existing users in database: {existing_count}")
    
    # Date range for user creation (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    dummy_users = []
    
    for i in range(num_users):
        first_name = random.choice(indian_first_names)
        last_name = random.choice(indian_last_names)
        city = random.choice(indian_cities)
        state = random.choice(indian_states)
        street = random.choice(street_prefixes)
        
        join_date = generate_random_date(start_date, end_date)
        
        user = {
            'name': f"{first_name} {last_name}",
            'email': generate_indian_email(first_name, last_name),
            'phone': generate_indian_phone(),
            'address': f"{random.randint(1, 999)}/{random.randint(1, 50)}, {street}",
            'city': city,
            'state': state,
            'zipcode': generate_indian_pincode(),
            'join_date': join_date,
            'created_at': join_date,
            'is_active': random.choice([True, True, True, True, False]),  # 80% active
            'loyalty_points': random.randint(0, 5000),
            'total_purchases': random.randint(0, 50),
            'last_purchase': generate_random_date(join_date, end_date) if random.random() > 0.3 else None,
            'email_notifications': True,  # Enable email notifications for festival offers
            'preferred_language': random.choice(['English', 'Hindi', 'Tamil', 'Telugu', 'Kannada', 'Malayalam'])
        }
        
        dummy_users.append(user)
        
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1} users...")
    
    # Insert users into database
    print("\nInserting users into database...")
    try:
        result = users.insert_many(dummy_users)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} users!")
        
        # Display final statistics
        total_users = users.count_documents({})
        active_users = users.count_documents({'is_active': True})
        print(f"\n{'='*50}")
        print(f"DATABASE STATISTICS")
        print(f"{'='*50}")
        print(f"Total Users: {total_users}")
        print(f"Active Users: {active_users}")
        print(f"New Users Added: {len(result.inserted_ids)}")
        print(f"{'='*50}\n")
        
        return result.inserted_ids
    except Exception as e:
        print(f"❌ Error inserting users: {e}")
        return []

if __name__ == '__main__':
    print("\n" + "="*60)
    print("INDIAN USERS GENERATOR FOR SALES SENSE AI")
    print("="*60)
    
    # Generate 50 users (you can change this number)
    user_ids = create_indian_users(50)
    
    if user_ids:
        print("✅ User generation completed successfully!")
        print("Users are ready to receive festival notification emails.\n")
    else:
        print("❌ User generation failed!\n")
    
    client.close()
